import {
  Accessibility,
  Briefcase,
  Building2,
  GraduationCap,
  LayoutGrid,
  Users,
} from 'lucide-react'

const CATEGORY_ICONS = {
  étudiant: GraduationCap,
  emploi: Briefcase,
  entreprise: Building2,
  femmes: Users,
  handicap: Accessibility,
  autres: LayoutGrid,
}

function getCategoryIcon(nom) {
  const key = nom?.toLowerCase().trim()
  return CATEGORY_ICONS[key] ?? LayoutGrid
}

/** Carte catégorie d'aides avec icône et compteur. */
export default function CategoryCard({ category }) {
  const Icon = getCategoryIcon(category.nom)

  return (
    <div className="group rounded-xl border border-border/60 bg-card p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-brand-border hover:shadow-md">
      <div className="mb-4 flex size-11 items-center justify-center rounded-xl bg-brand-light transition-colors group-hover:bg-brand-lighter">
        <Icon className="size-5 text-brand" />
      </div>
      <h3 className="font-semibold text-foreground">{category.nom}</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        {category.nombre_aides} aide{category.nombre_aides !== 1 ? 's' : ''}
      </p>
    </div>
  )
}
