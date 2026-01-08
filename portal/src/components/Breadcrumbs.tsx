import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

export interface BreadcrumbItem {
  label: string
  path?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  if (items.length === 0) return null

  return (
    <nav className="flex items-center gap-2 text-sm text-neutral-600 mb-6">
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        const isClickable = item.path && !isLast

        return (
          <div key={index} className="flex items-center gap-2">
            {isClickable ? (
              <Link
                to={item.path!}
                className="hover:text-primary-600 transition-colors font-medium"
              >
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? 'text-neutral-900 font-semibold' : 'text-neutral-500'}>
                {item.label}
              </span>
            )}
            {!isLast && (
              <ChevronRight size={16} className="text-neutral-400" />
            )}
          </div>
        )
      })}
    </nav>
  )
}

