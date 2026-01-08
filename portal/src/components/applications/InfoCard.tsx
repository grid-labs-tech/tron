import { Info } from 'lucide-react'
import { ReactNode } from 'react'

interface InfoCardProps {
  children: ReactNode
}

export function InfoCard({ children }: InfoCardProps) {
  return (
    <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-start gap-3">
        <div className="p-1.5 bg-blue-100 rounded-lg">
          <Info className="text-blue-600" size={18} />
        </div>
        <div className="flex-1">
          {children}
        </div>
      </div>
    </div>
  )
}

