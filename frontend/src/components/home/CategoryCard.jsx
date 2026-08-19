import {
  Accessibility,
  Briefcase,
  Building2,
  GraduationCap,
  LayoutGrid,
  Users,
} from 'lucide-react'

function renderCategoryIcon(nom) {
  const key = nom?.toLowerCase().trim()
  switch (key) {
    case 'étudiant':
      return <GraduationCap className="size-5 text-brand" />
    case 'emploi':
      return <Briefcase className="size-5 text-brand" />
    case 'entreprise':
      return <Building2 className="size-5 text-brand" />
    case 'femmes':
      return <Users className="size-5 text-brand" />
    case 'handicap':
      return <Accessibility className="size-5 text-brand" />
    default:
      return <LayoutGrid className="size-5 text-brand" />
  }
}

/** Carte catégorie d'aides avec icône et compteur. */
export default function CategoryCard({ category }) {
  return (
    <div className="group rounded-xl border border-border/60 bg-card p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-brand-border hover:shadow-md">
      <div className="mb-4 flex size-11 items-center justify-center rounded-xl bg-brand-light transition-colors group-hover:bg-brand-lighter">
        {renderCategoryIcon(category.nom)}
      </div>
      <h3 className="font-semibold text-foreground">{category.nom}</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        {category.nombre_aides} aide{category.nombre_aides !== 1 ? 's' : ''}
      </p>
    </div>
  )
}
