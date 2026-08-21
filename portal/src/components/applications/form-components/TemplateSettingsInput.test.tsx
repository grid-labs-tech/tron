import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TemplateSettingsInput } from './TemplateSettingsInput'
import type { TemplateSettingsGroup } from '../../../features/templates'

const groups: TemplateSettingsGroup[] = [
  {
    template_uuid: 'tmpl-1',
    template_name: 'Webapp Deployment',
    template_slug: 'webapp_deployment',
    settings: [
      { name: 'enable_pdb', description: 'Attach a debug sidecar', type: 'boolean' },
      { name: 'region', description: 'Cloud region', type: 'string' },
    ],
  },
  {
    template_uuid: 'tmpl-2',
    template_name: 'Webapp Service',
    template_slug: 'webapp_service',
    settings: [{ name: 'region', type: 'string' }],
  },
]

describe('TemplateSettingsInput', () => {
  it('renders settings grouped by template name', () => {
    render(<TemplateSettingsInput groups={groups} values={{}} onChange={vi.fn()} />)

    expect(screen.getByText('Webapp Deployment')).toBeInTheDocument()
    expect(screen.getByText('Webapp Service')).toBeInTheDocument()
    expect(screen.getByText('Attach a debug sidecar')).toBeInTheDocument()
  })

  it('updates boolean and string values nested by slug', () => {
    const onChange = vi.fn()
    render(<TemplateSettingsInput groups={groups} values={{}} onChange={onChange} />)

    fireEvent.click(screen.getByRole('checkbox'))
    expect(onChange).toHaveBeenCalledWith({
      webapp_deployment: { enable_pdb: true },
    })

    const regionInputs = screen.getAllByRole('textbox')
    fireEvent.change(regionInputs[0], { target: { value: 'us-east-1' } })
    expect(onChange).toHaveBeenCalledWith({
      webapp_deployment: { region: 'us-east-1' },
    })
  })

  it('renders nothing when there are no template settings', () => {
    const { container } = render(
      <TemplateSettingsInput groups={[]} values={{}} onChange={vi.fn()} />
    )
    expect(container).toBeEmptyDOMElement()
  })
})
