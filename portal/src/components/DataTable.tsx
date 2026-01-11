import { ReactNode, useState, useMemo } from 'react'
import { Search, X, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'
import ActionMenu, { ActionMenuItem } from './ActionMenu'

export interface Column<T> {
  key: keyof T | string
  label: string
  render?: (item: T) => ReactNode
  searchable?: boolean
  sortable?: boolean
  width?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  isLoading?: boolean
  emptyMessage?: string
  loadingColor?: string
  getRowKey: (item: T) => string | number
  actions?: (item: T) => ActionMenuItem[]
  searchable?: boolean
  searchPlaceholder?: string
}

function DataTable<T>({
  columns,
  data,
  isLoading = false,
  emptyMessage = 'Nenhum item encontrado',
  loadingColor = 'blue',
  getRowKey,
  actions,
  searchable = true,
  searchPlaceholder = 'Buscar...',
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState<keyof T | string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  const colorClasses: Record<string, { spinner: string }> = {
    blue: { spinner: 'border-blue-200 border-t-blue-600' },
    indigo: { spinner: 'border-indigo-200 border-t-indigo-600' },
    sky: { spinner: 'border-sky-200 border-t-sky-600' },
    violet: { spinner: 'border-violet-200 border-t-violet-600' },
    purple: { spinner: 'border-purple-200 border-t-purple-600' },
  }

  const spinnerClass = colorClasses[loadingColor]?.spinner || colorClasses.blue.spinner
  const colSpan = columns.length + (actions ? 1 : 0)

  const filteredData = useMemo(() => {
    let result = data

    // Apply search filter
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase().trim()
      const searchableColumns = columns.filter((col) => col.searchable !== false)

      result = data.filter((item) => {
        return searchableColumns.some((column) => {
          const value = item[column.key as keyof T]
          if (value === null || value === undefined) return false

          if (column.render) {
            const stringValue = String(value).toLowerCase()
            return stringValue.includes(searchLower)
          }

          const stringValue = String(value).toLowerCase()
          return stringValue.includes(searchLower)
        })
      })
    }

    // Apply sorting
    if (sortColumn) {
      const column = columns.find((col) => col.key === sortColumn)
      if (column && column.sortable === true) {
        result = [...result].sort((a, b) => {
          const aValue = a[sortColumn as keyof T]
          const bValue = b[sortColumn as keyof T]

          // Handle null/undefined values
          if (aValue === null || aValue === undefined) return 1
          if (bValue === null || bValue === undefined) return -1

          // Numeric comparison
          if (typeof aValue === 'number' && typeof bValue === 'number') {
            return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
          }

          // String comparison
          const aStr = String(aValue).toLowerCase()
          const bStr = String(bValue).toLowerCase()

          if (sortDirection === 'asc') {
            return aStr.localeCompare(bStr)
          } else {
            return bStr.localeCompare(aStr)
          }
        })
      }
    }

    return result
  }, [data, searchTerm, columns, sortColumn, sortDirection])

  const handleSort = (columnKey: keyof T | string) => {
    const column = columns.find((col) => col.key === columnKey)
    if (!column || column.sortable !== true) return

    if (sortColumn === columnKey) {
      // Toggle direction if already sorting by this column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      // New column, start with ascending
      setSortColumn(columnKey)
      setSortDirection('asc')
    }
  }

  const getSortIcon = (columnKey: keyof T | string) => {
    if (sortColumn !== columnKey) {
      return <ArrowUpDown className="h-3 w-3 text-slate-400" />
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="h-3 w-3 text-primary-600" />
    ) : (
      <ArrowDown className="h-3 w-3 text-primary-600" />
    )
  }

  return (
    <div className="glass-effect rounded-xl shadow-soft overflow-hidden w-full">
      {searchable && (
        <div className="px-6 py-4 border-b border-neutral-200/60 bg-gradient-subtle">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-neutral-400" />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10 pr-10"
              placeholder={searchPlaceholder}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-neutral-400 hover:text-neutral-600 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      )}

      <div className="overflow-x-auto w-full">
        <table className="min-w-full divide-y divide-neutral-200">
          <thead className="bg-gradient-subtle">
            <tr>
              {columns.map((column) => {
                const isSortable = column.sortable === true
                return (
                  <th
                    key={String(column.key)}
                    className={`px-6 py-3.5 text-left text-xs font-semibold text-neutral-700 uppercase tracking-wider ${
                      isSortable ? 'cursor-pointer hover:bg-primary-50/50 transition-colors select-none' : ''
                    }`}
                    style={column.width ? { width: column.width } : undefined}
                    onClick={() => isSortable && handleSort(column.key)}
                  >
                    <div className="flex items-center gap-2">
                      <span>{column.label}</span>
                      {isSortable && getSortIcon(column.key)}
                    </div>
                  </th>
                )
              })}
              {actions && (
                <th className="px-6 py-3.5 text-right text-xs font-semibold text-neutral-700 uppercase tracking-wider">
                  Ações
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-neutral-100">
            {isLoading ? (
              <tr>
                <td colSpan={colSpan} className="px-6 py-12 text-center text-neutral-400">
                  <div className="flex items-center justify-center gap-2">
                    <div className={`animate-spin rounded-full h-5 w-5 border-2 ${spinnerClass}`}></div>
                    <span className="text-sm text-neutral-600">Carregando...</span>
                  </div>
                </td>
              </tr>
            ) : filteredData.length === 0 ? (
              <tr>
                <td colSpan={colSpan} className="px-6 py-12 text-center text-neutral-400 text-sm">
                  {searchTerm ? 'Nenhum resultado encontrado para a busca' : emptyMessage}
                </td>
              </tr>
            ) : (
              filteredData.map((item) => (
                <tr key={getRowKey(item)} className="hover:bg-primary-50/30 transition-colors border-b border-neutral-50">
                  {columns.map((column) => (
                    <td
                      key={String(column.key)}
                      className="px-6 py-4 whitespace-nowrap"
                      style={column.width ? { width: column.width } : undefined}
                    >
                      {column.render ? (
                        column.render(item)
                      ) : (
                        <div className="text-sm text-neutral-700">
                          {String(item[column.key as keyof T] ?? '')}
                        </div>
                      )}
                    </td>
                  ))}
                  {actions && (
                    <td className="px-6 py-3.5 whitespace-nowrap">
                      <div className="flex justify-end">
                        <ActionMenu items={actions(item)} />
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default DataTable

