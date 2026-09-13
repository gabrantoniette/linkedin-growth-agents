'use client'

import { Button } from '@/components/ui/button'
import Icon from '@/components/ui/icon'
import Paragraph from '@/components/ui/typography/Paragraph'
import useAIChatStreamHandler from '@/hooks/useAIStreamHandler'
import { useStore } from '@/store'
import { type RunRequirement } from '@/types/os'

/**
 * Renders the string arguments of the held tool call.
 *
 * The post body is the argument that matters for `publish_post`, and it is the
 * only chance to read what goes out before it goes out, so it is shown in full
 * rather than truncated. Other tools get the same treatment: whatever the
 * argument is, the person approving should see all of it.
 */
const ToolArguments = ({ requirement }: { requirement: RunRequirement }) => {
  const args = requirement.tool_execution?.tool_args
  if (!args || Object.keys(args).length === 0) {
    return (
      <Paragraph size="xsmall" className="text-muted">
        (no arguments)
      </Paragraph>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {Object.entries(args).map(([name, value]) => (
        <div key={name} className="flex flex-col gap-1">
          <span className="font-dmmono text-xs uppercase tracking-wide text-muted">
            {name}
          </span>
          <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap break-words rounded-md bg-background p-3 font-geist text-xs text-primary">
            {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  )
}

/**
 * The gate in front of an irreversible action.
 *
 * A tool marked `requires_confirmation=True` on the Python side stops the run
 * and the server waits. The terminal chat has always had this prompt; this is
 * the same gate for the browser, which previously received the pause event,
 * ignored it, and left the run parked with nothing on screen.
 *
 * Two deliberate choices, both matching the CLI:
 *
 * - **Nothing is pre-selected.** There is no default action and no focused
 *   primary button, so an accidental Enter cannot publish.
 * - **Declining continues the run**, it does not cancel it. The agent gets to
 *   say what it will do instead, and no run is left paused forever.
 */
const ApprovalRequest = () => {
  const pendingApproval = useStore((state) => state.pendingApproval)
  const isResolvingApproval = useStore((state) => state.isResolvingApproval)
  const { handleApproval } = useAIChatStreamHandler()

  if (!pendingApproval) return null

  const { requirements } = pendingApproval
  const toolNames = requirements
    .map((requirement) => requirement.tool_execution?.tool_name)
    .filter(Boolean)
    .join(', ')

  return (
    <div className="mx-auto mb-2 w-full max-w-2xl rounded-xl border border-destructive/60 bg-accent p-4">
      <div className="flex items-center gap-2">
        <Icon type="agent" size="xs" className="text-destructive" />
        <span className="text-sm font-medium uppercase tracking-wide text-primary">
          Approval required
        </span>
      </div>

      <Paragraph size="xsmall" className="mt-2 text-muted">
        The run is paused. It will not continue until you answer, and this
        action cannot be undone once it runs.
      </Paragraph>

      <div className="mt-3 flex flex-col gap-3">
        {requirements.map((requirement, index) => (
          <div
            key={requirement.id ?? index}
            className="rounded-lg border border-primary/10 p-3"
          >
            <div className="mb-2 flex items-baseline gap-2">
              <span className="font-dmmono text-xs text-primary">
                {requirement.tool_execution?.tool_name ?? 'unknown tool'}
              </span>
              {requirement.member_agent_name && (
                <span className="text-xs text-muted">
                  via {requirement.member_agent_name}
                </span>
              )}
            </div>
            <ToolArguments requirement={requirement} />
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={isResolvingApproval}
          onClick={() => handleApproval(false)}
        >
          Decline
        </Button>
        <Button
          variant="destructive"
          size="sm"
          disabled={isResolvingApproval}
          onClick={() => handleApproval(true)}
        >
          {isResolvingApproval ? 'Running…' : `Run ${toolNames || 'the tool'}`}
        </Button>
      </div>
    </div>
  )
}

export default ApprovalRequest
