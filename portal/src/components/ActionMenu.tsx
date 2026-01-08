import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { MoreVertical } from 'lucide-react'
import { ReactNode } from 'react'

export interface ActionMenuItem {
  label: string
  icon?: ReactNode
  onClick: () => void
  variant?: 'default' | 'danger' | 'warning'
}

interface ActionMenuProps {
  items: ActionMenuItem[]
}

function ActionMenu({ items }: ActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [menuPosition, setMenuPosition] = useState<{ top: number; right: number }>({ top: 0, right: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setMenuPosition({
        top: rect.bottom + 4,
        right: window.innerWidth - rect.right,
      })
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    const handleScroll = () => {
      setIsOpen(false)
    }

    document.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('scroll', handleScroll, true)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('scroll', handleScroll, true)
    }
  }, [isOpen])

  const handleItemClick = (item: ActionMenuItem) => {
    item.onClick()
    setIsOpen(false)
  }

  const handleButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation()

    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setMenuPosition({
        top: rect.bottom + 4,
        right: window.innerWidth - rect.right,
      })
    }

    setIsOpen(!isOpen)
  }

  const menuContent = isOpen && items.length > 0 ? (
    <div
      ref={menuRef}
      className="fixed w-48 bg-white rounded-lg shadow-soft-lg border border-slate-200/60 py-1 z-[9999] animate-zoom-in"
      style={{
        top: `${menuPosition.top}px`,
        right: `${menuPosition.right}px`,
      }}
    >
      {items.map((item, index) => (
        <button
          key={index}
          onClick={() => handleItemClick(item)}
          className={`
            w-full px-4 py-2 text-left text-sm flex items-center gap-2.5
            transition-colors first:rounded-t-lg last:rounded-b-lg
            ${
              item.variant === 'danger'
                ? 'text-red-600 hover:bg-red-50/50'
                : item.variant === 'warning'
                ? 'text-amber-600 hover:bg-amber-50/50'
                : 'text-slate-700 hover:bg-slate-50'
            }
          `}
        >
          {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
          <span>{item.label}</span>
        </button>
      ))}
    </div>
  ) : null

  return (
    <>
      <button
        ref={buttonRef}
        onClick={handleButtonClick}
        className="p-1.5 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
        aria-label="Ações"
      >
        <MoreVertical size={18} />
      </button>

      {typeof document !== 'undefined' && createPortal(menuContent, document.body)}
    </>
  )
}

export default ActionMenu

