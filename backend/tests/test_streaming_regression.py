# -*- coding: utf-8 -*-
"""Tests de non-régression du streaming Dify et de la sauvegarde du message bot.

Couvre :
1. Les espaces de début de chunk sont préservés (pas de `.strip()` par chunk,
   pas d'espace artificiel ajouté entre chunks).
2. Les retours à la ligne du message final (`bot_msg.contenu`) sont préservés.
3. La limite `MAX_RESPONSE_CHARS` reste respectée par la troncature.
4. `_clean_text` n'a pas été modifié (il reste utilisé pour les titres).
"""

import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.utilisateurs import Utilisateur
from app.services.chat_service import MAX_RESPONSE_CHARS, _clean_text, _preserve_text
from app.services.conversation_engine import (
    ConversationDecision,
    ConversationMeta,
    ConversationState,
    IntentCategory,
)
from app.services import response_generator as rg
from app.services.response_generator import response_generator

# Chunks simulés issus de Dify, porteurs d'espaces en début de chunk.
GREETING_CHUNKS = ["Bonjour", " !", " Je", " suis", " AidFinder"]

NEWLINES_BODY = (
    "Bonjour !\n\n"
    "Je peux vous aider.\n\n"
    "- Emploi\n"
    "- Formation\n"
    "- Mobilité"
)


def _make_decision() -> ConversationDecision:
    return ConversationDecision(
        intent=IntentCategory.GREETING,
        new_state=ConversationState.DISCUSSING,
        should_ask_question=False,
        field_to_ask=None,
        extracted_info={},
        merged_profile={},
        clarification_needed=False,
    )


async def _collect_stream(decision, meta, message="Bonjour"):
    chunks = []
    async for chunk in response_generator.generate_stream(decision, meta, message):
        chunks.append(chunk)
    return chunks


class StreamChunksRegressionTestCase(unittest.TestCase):
    """Le générateur transmet chaque chunk exactement comme Dify le fournit."""

    def _run(self, chunks_sim, message="Bonjour"):
        decision = _make_decision()
        meta = ConversationMeta()

        def fake_stream(message, conversation_id=None, inputs=None):
            for chunk in chunks_sim:
                yield {
                    "success": True,
                    "answer": chunk,
                    "conversation_id": "cs1",
                    "raw": {},
                }

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message_stream.side_effect = fake_stream
            chunks = asyncio.run(_collect_stream(decision, meta, message))
        return chunks, meta

    def test_spaces_before_chunks_are_preserved(self):
        """\"Bonjour\" + \" !\" + \" Je\" + \" suis\" + \" AidFinder\"
        doit produire \"Bonjour ! Je suis AidFinder\" et non \"Bonjour!JesuisAidFinder\"."""
        chunks, meta = self._run(GREETING_CHUNKS)

        # Chaque chunk est retransmis tel quel, sans .strip() et sans espace ajouté.
        self.assertEqual(chunks, GREETING_CHUNKS)

        full = "".join(chunks)
        self.assertEqual(full, "Bonjour ! Je suis AidFinder")
        self.assertNotEqual(full, "Bonjour!JesuisAidFinder")
        self.assertEqual(meta.dify_conversation_id, "cs1")

    def test_newlines_are_preserved(self):
        """Les retours à la ligne présents dans les chunks survivent à la concaténation."""
        size = 7
        chunks_sim = [
            NEWLINES_BODY[i:i + size] for i in range(0, len(NEWLINES_BODY), size)
        ]
        chunks, _ = self._run(chunks_sim)

        self.assertEqual("".join(chunks), NEWLINES_BODY)
        self.assertIn("\n\n", "".join(chunks))


class ChatServiceSaveRegressionTestCase(unittest.TestCase):
    """Le contenu final enregistré dans bot_msg.contenu conserve espaces et \\n."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        self.user = Utilisateur(
            nom="Test",
            email="streaming@example.com",
            mot_de_passe_hash="x",
            role="utilisateur",
            statut_compte="actif",
        )
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _run_stream(self, chunks_sim, message="Bonjour"):
        from app.services.chat_service import chat_service

        def fake_stream(message, conversation_id=None, inputs=None):
            for chunk in chunks_sim:
                yield {
                    "success": True,
                    "answer": chunk,
                    "conversation_id": "cs1",
                    "raw": {},
                }

        async def run():
            events = []
            results = []
            async for ev in chat_service.handle_message_stream(self.db, self.user, message):
                events.append(ev)
                if ev.get("type") == "done":
                    results.append(ev["data"])
            return events, results

        with patch.object(rg, "dify_client") as mock_dify:
            mock_dify.send_message_stream.side_effect = fake_stream
            return asyncio.run(run())

    def test_stream_chunks_forwarded_exactly(self):
        events, results = self._run_stream(GREETING_CHUNKS)
        chunks = [e["data"] for e in events if e.get("type") == "chunk"]
        self.assertEqual(chunks, GREETING_CHUNKS)
        self.assertEqual(
            results[0]["bot_message"]["contenu"], "Bonjour ! Je suis AidFinder"
        )
        self.assertNotEqual(
            results[0]["bot_message"]["contenu"], "Bonjour!JesuisAidFinder"
        )

    def test_bot_message_keeps_newlines_and_bullet_list(self):
        size = 7
        chunks_sim = [
            NEWLINES_BODY[i:i + size] for i in range(0, len(NEWLINES_BODY), size)
        ]
        _, results = self._run_stream(chunks_sim)
        self.assertEqual(results[0]["bot_message"]["contenu"], NEWLINES_BODY)


class TruncationHelperTestCase(unittest.TestCase):
    """La troncature du message bot préserve les sauts de ligne et la limite."""

    def test_preserve_text_keeps_spaces_and_newlines(self):
        text = "Bonjour !\n\nJe peux vous aider.\n\n- Emploi\n- Formation"
        self.assertEqual(_preserve_text(text), text)

    def test_preserve_text_respects_limit(self):
        text = "Mot " * 1000  # 4000 caractères
        truncated = _preserve_text(text, MAX_RESPONSE_CHARS)
        self.assertTrue(truncated.endswith("..."))
        base = truncated[:-3]
        # La troncature ne dépasse jamais le plafond demandé.
        self.assertLessEqual(len(base), MAX_RESPONSE_CHARS)
        # Le texte conservé est un préfixe exact du contenu original.
        self.assertTrue(text.startswith(base))

    def test_clean_text_unchanged(self):
        # _clean_text reste en place et aplatit toujours les sauts de ligne
        # pour les autres usages (titres, historique...).
        self.assertEqual(
            _clean_text("Bonjour !\n\n  Je  peux  aider. "),
            "Bonjour ! Je peux aider.",
        )


if __name__ == "__main__":
    unittest.main()