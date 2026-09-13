import { useCallback } from 'react'

import { APIRoutes } from '@/api/routes'

import useChatActions from '@/hooks/useChatActions'
import { useStore } from '../store'
import {
  RunEvent,
  RunResponseContent,
  type RunRequirement,
  type RunResponse
} from '@/types/os'
import { constructEndpointUrl } from '@/lib/constructEndpointUrl'
import useAIResponseStream from './useAIResponseStream'
import { ToolCall } from '@/types/os'
import { useQueryState } from 'nuqs'
import { getJsonMarkdown } from '@/lib/utils'

/**
 * Per-stream bookkeeping.
 *
 * `lastContent` and `newSessionId` used to be closure variables inside the
 * single stream call. A run that pauses for approval produces a SECOND stream
 * when it resumes, and both streams need the same chunk handling, so the state
 * moved into an object the handler mutates. One object per stream: a resumed
 * stream starts with an empty `lastContent`, exactly like a fresh one.
 */
interface StreamContext {
  lastContent: string
  newSessionId: string | null
  sessionName: string
}

const useAIChatStreamHandler = () => {
  const setMessages = useStore((state) => state.setMessages)
  const { addMessage, focusChatInput } = useChatActions()
  const [agentId] = useQueryState('agent')
  const [teamId] = useQueryState('team')
  const [sessionId, setSessionId] = useQueryState('session')
  const selectedEndpoint = useStore((state) => state.selectedEndpoint)
  const authToken = useStore((state) => state.authToken)
  const mode = useStore((state) => state.mode)
  const setStreamingErrorMessage = useStore(
    (state) => state.setStreamingErrorMessage
  )
  const setIsStreaming = useStore((state) => state.setIsStreaming)
  const setSessionsData = useStore((state) => state.setSessionsData)
  const pendingApproval = useStore((state) => state.pendingApproval)
  const setPendingApproval = useStore((state) => state.setPendingApproval)
  const setIsResolvingApproval = useStore(
    (state) => state.setIsResolvingApproval
  )
  const { streamResponse } = useAIResponseStream()

  const updateMessagesWithErrorState = useCallback(() => {
    setMessages((prevMessages) => {
      const newMessages = [...prevMessages]
      const lastMessage = newMessages[newMessages.length - 1]
      if (lastMessage && lastMessage.role === 'agent') {
        lastMessage.streamingError = true
      }
      return newMessages
    })
  }, [setMessages])

  /**
   * Processes a new tool call and adds it to the message
   * @param toolCall - The tool call to add
   * @param prevToolCalls - The previous tool calls array
   * @returns Updated tool calls array
   */
  const processToolCall = useCallback(
    (toolCall: ToolCall, prevToolCalls: ToolCall[] = []) => {
      const toolCallId =
        toolCall.tool_call_id || `${toolCall.tool_name}-${toolCall.created_at}`

      const existingToolCallIndex = prevToolCalls.findIndex(
        (tc) =>
          (tc.tool_call_id && tc.tool_call_id === toolCall.tool_call_id) ||
          (!tc.tool_call_id &&
            toolCall.tool_name &&
            toolCall.created_at &&
            `${tc.tool_name}-${tc.created_at}` === toolCallId)
      )
      if (existingToolCallIndex >= 0) {
        const updatedToolCalls = [...prevToolCalls]
        updatedToolCalls[existingToolCallIndex] = {
          ...updatedToolCalls[existingToolCallIndex],
          ...toolCall
        }
        return updatedToolCalls
      } else {
        return [...prevToolCalls, toolCall]
      }
    },
    []
  )

  /**
   * Processes tool calls from a chunk, handling both single tool object and tools array formats
   * @param chunk - The chunk containing tool call data
   * @param existingToolCalls - The existing tool calls array
   * @returns Updated tool calls array
   */
  const processChunkToolCalls = useCallback(
    (
      chunk: RunResponseContent | RunResponse,
      existingToolCalls: ToolCall[] = []
    ) => {
      let updatedToolCalls = [...existingToolCalls]
      // Handle new single tool object format
      if (chunk.tool) {
        updatedToolCalls = processToolCall(chunk.tool, updatedToolCalls)
      }
      // Handle legacy tools array format
      if (chunk.tools && chunk.tools.length > 0) {
        for (const toolCall of chunk.tools) {
          updatedToolCalls = processToolCall(toolCall, updatedToolCalls)
        }
      }

      return updatedToolCalls
    },
    [processToolCall]
  )

  /**
   * Handles one streamed chunk. Shared by the original run and by the
   * continuation that follows an approval, so both behave identically.
   */
  const processChunk = useCallback(
    (chunk: RunResponse, ctx: StreamContext) => {
      if (
        chunk.event === RunEvent.RunStarted ||
        chunk.event === RunEvent.TeamRunStarted ||
        chunk.event === RunEvent.ReasoningStarted ||
        chunk.event === RunEvent.TeamReasoningStarted
      ) {
        ctx.newSessionId = chunk.session_id as string
        setSessionId(chunk.session_id as string)
        if (
          (!sessionId || sessionId !== chunk.session_id) &&
          chunk.session_id
        ) {
          const sessionData = {
            session_id: chunk.session_id as string,
            session_name: ctx.sessionName,
            created_at: chunk.created_at
          }
          setSessionsData((prevSessionsData) => {
            const sessionExists = prevSessionsData?.some(
              (session) => session.session_id === chunk.session_id
            )
            if (sessionExists) {
              return prevSessionsData
            }
            return [sessionData, ...(prevSessionsData ?? [])]
          })
        }
      } else if (
        chunk.event === RunEvent.ToolCallStarted ||
        chunk.event === RunEvent.TeamToolCallStarted ||
        chunk.event === RunEvent.ToolCallCompleted ||
        chunk.event === RunEvent.TeamToolCallCompleted
      ) {
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages]
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage && lastMessage.role === 'agent') {
            lastMessage.tool_calls = processChunkToolCalls(
              chunk,
              lastMessage.tool_calls
            )
          }
          return newMessages
        })
      } else if (
        // The run stopped and will not continue on its own: a tool declared
        // `requires_confirmation=True` is waiting for an answer. Park the
        // requirements so the approval panel can render them. The stream ends
        // right after this, which is why nothing used to appear on screen.
        chunk.event === RunEvent.TeamRunPaused ||
        chunk.event === RunEvent.RunPaused
      ) {
        const requirements = (chunk.requirements ?? []).filter(
          (requirement) => requirement.tool_execution
        )
        const runId = chunk.run_id
        const pausedSessionId =
          chunk.session_id ?? ctx.newSessionId ?? sessionId

        if (!requirements.length || !runId || !pausedSessionId) {
          // Paused for something this UI cannot answer (external execution, or
          // a payload without the ids needed to resume). Say so instead of
          // leaving the user in front of a run that looks finished.
          updateMessagesWithErrorState()
          setStreamingErrorMessage(
            'The run is paused waiting for something this interface cannot provide. Continue it from the terminal with `uv run linkedin chat`.'
          )
          return
        }

        setPendingApproval({
          runId,
          sessionId: pausedSessionId,
          requirements
        })
      } else if (
        chunk.event === RunEvent.TeamRunContinued ||
        chunk.event === RunEvent.RunContinued
      ) {
        // The server accepted the answer and picked the run back up. Nothing to
        // render: the content that follows arrives as ordinary RunContent.
      } else if (
        chunk.event === RunEvent.RunContent ||
        chunk.event === RunEvent.TeamRunContent
      ) {
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages]
          const lastMessage = newMessages[newMessages.length - 1]
          if (
            lastMessage &&
            lastMessage.role === 'agent' &&
            typeof chunk.content === 'string'
          ) {
            const uniqueContent = chunk.content.replace(ctx.lastContent, '')
            lastMessage.content += uniqueContent
            ctx.lastContent = chunk.content

            // Handle tool calls streaming
            lastMessage.tool_calls = processChunkToolCalls(
              chunk,
              lastMessage.tool_calls
            )
            if (chunk.extra_data?.reasoning_steps) {
              lastMessage.extra_data = {
                ...lastMessage.extra_data,
                reasoning_steps: chunk.extra_data.reasoning_steps
              }
            }

            if (chunk.extra_data?.references) {
              lastMessage.extra_data = {
                ...lastMessage.extra_data,
                references: chunk.extra_data.references
              }
            }

            lastMessage.created_at = chunk.created_at ?? lastMessage.created_at
            if (chunk.images) {
              lastMessage.images = chunk.images
            }
            if (chunk.videos) {
              lastMessage.videos = chunk.videos
            }
            if (chunk.audio) {
              lastMessage.audio = chunk.audio
            }
          } else if (
            lastMessage &&
            lastMessage.role === 'agent' &&
            typeof chunk?.content !== 'string' &&
            chunk.content !== null
          ) {
            const jsonBlock = getJsonMarkdown(chunk?.content)

            lastMessage.content += jsonBlock
            ctx.lastContent = jsonBlock
          } else if (
            chunk.response_audio?.transcript &&
            typeof chunk.response_audio?.transcript === 'string'
          ) {
            const transcript = chunk.response_audio.transcript
            lastMessage.response_audio = {
              ...lastMessage.response_audio,
              transcript: lastMessage.response_audio?.transcript + transcript
            }
          }
          return newMessages
        })
      } else if (
        chunk.event === RunEvent.ReasoningStep ||
        chunk.event === RunEvent.TeamReasoningStep
      ) {
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages]
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage && lastMessage.role === 'agent') {
            const existingSteps = lastMessage.extra_data?.reasoning_steps ?? []
            const incomingSteps = chunk.extra_data?.reasoning_steps ?? []
            lastMessage.extra_data = {
              ...lastMessage.extra_data,
              reasoning_steps: [...existingSteps, ...incomingSteps]
            }
          }
          return newMessages
        })
      } else if (
        chunk.event === RunEvent.ReasoningCompleted ||
        chunk.event === RunEvent.TeamReasoningCompleted
      ) {
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages]
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage && lastMessage.role === 'agent') {
            if (chunk.extra_data?.reasoning_steps) {
              lastMessage.extra_data = {
                ...lastMessage.extra_data,
                reasoning_steps: chunk.extra_data.reasoning_steps
              }
            }
          }
          return newMessages
        })
      } else if (
        chunk.event === RunEvent.RunError ||
        chunk.event === RunEvent.TeamRunError ||
        chunk.event === RunEvent.TeamRunCancelled
      ) {
        updateMessagesWithErrorState()
        const errorContent =
          (chunk.content as string) ||
          (chunk.event === RunEvent.TeamRunCancelled
            ? 'Run cancelled'
            : 'Error during run')
        setStreamingErrorMessage(errorContent)
        if (ctx.newSessionId) {
          setSessionsData(
            (prevSessionsData) =>
              prevSessionsData?.filter(
                (session) => session.session_id !== ctx.newSessionId
              ) ?? null
          )
        }
      } else if (
        chunk.event === RunEvent.UpdatingMemory ||
        chunk.event === RunEvent.TeamMemoryUpdateStarted ||
        chunk.event === RunEvent.TeamMemoryUpdateCompleted
      ) {
        // No-op for now; could surface a lightweight UI indicator in the future
      } else if (
        chunk.event === RunEvent.RunCompleted ||
        chunk.event === RunEvent.TeamRunCompleted
      ) {
        setMessages((prevMessages) => {
          const newMessages = prevMessages.map((message, index) => {
            if (index === prevMessages.length - 1 && message.role === 'agent') {
              let updatedContent: string
              if (typeof chunk.content === 'string') {
                updatedContent = chunk.content
              } else {
                try {
                  updatedContent = JSON.stringify(chunk.content)
                } catch {
                  updatedContent = 'Error parsing response'
                }
              }
              return {
                ...message,
                content: updatedContent,
                tool_calls: processChunkToolCalls(chunk, message.tool_calls),
                images: chunk.images ?? message.images,
                videos: chunk.videos ?? message.videos,
                response_audio: chunk.response_audio,
                created_at: chunk.created_at ?? message.created_at,
                extra_data: {
                  reasoning_steps:
                    chunk.extra_data?.reasoning_steps ??
                    message.extra_data?.reasoning_steps,
                  references:
                    chunk.extra_data?.references ??
                    message.extra_data?.references
                }
              }
            }
            return message
          })
          return newMessages
        })
      }
    },
    [
      processChunkToolCalls,
      sessionId,
      setMessages,
      setPendingApproval,
      setSessionId,
      setSessionsData,
      setStreamingErrorMessage,
      updateMessagesWithErrorState
    ]
  )

  const authHeaders = useCallback(() => {
    const headers: Record<string, string> = {}
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`
    }
    return headers
  }, [authToken])

  const handleStreamResponse = useCallback(
    async (input: string | FormData) => {
      setIsStreaming(true)
      // A new question abandons any approval still on screen: it belonged to the
      // previous run, and answering it after this point would resume a run the
      // user has moved on from.
      setPendingApproval(null)

      const formData = input instanceof FormData ? input : new FormData()
      if (typeof input === 'string') {
        formData.append('message', input)
      }

      setMessages((prevMessages) => {
        if (prevMessages.length >= 2) {
          const lastMessage = prevMessages[prevMessages.length - 1]
          const secondLastMessage = prevMessages[prevMessages.length - 2]
          if (
            lastMessage.role === 'agent' &&
            lastMessage.streamingError &&
            secondLastMessage.role === 'user'
          ) {
            return prevMessages.slice(0, -2)
          }
        }
        return prevMessages
      })

      addMessage({
        role: 'user',
        content: formData.get('message') as string,
        created_at: Math.floor(Date.now() / 1000)
      })

      addMessage({
        role: 'agent',
        content: '',
        tool_calls: [],
        streamingError: false,
        created_at: Math.floor(Date.now() / 1000) + 1
      })

      const ctx: StreamContext = {
        lastContent: '',
        newSessionId: sessionId,
        sessionName: formData.get('message') as string
      }

      try {
        const endpointUrl = constructEndpointUrl(selectedEndpoint)

        let RunUrl: string | null = null

        if (mode === 'team' && teamId) {
          RunUrl = APIRoutes.TeamRun(endpointUrl, teamId)
        } else if (mode === 'agent' && agentId) {
          RunUrl = APIRoutes.AgentRun(endpointUrl).replace(
            '{agent_id}',
            agentId
          )
        }

        if (!RunUrl) {
          updateMessagesWithErrorState()
          setStreamingErrorMessage('Please select an agent or team first.')
          setIsStreaming(false)
          return
        }

        formData.append('stream', 'true')
        formData.append('session_id', sessionId ?? '')

        await streamResponse({
          apiUrl: RunUrl,
          headers: authHeaders(),
          requestBody: formData,
          onChunk: (chunk: RunResponse) => processChunk(chunk, ctx),
          onError: (error) => {
            updateMessagesWithErrorState()
            setStreamingErrorMessage(error.message)
            if (ctx.newSessionId) {
              setSessionsData(
                (prevSessionsData) =>
                  prevSessionsData?.filter(
                    (session) => session.session_id !== ctx.newSessionId
                  ) ?? null
              )
            }
          },
          onComplete: () => {}
        })
      } catch (error) {
        updateMessagesWithErrorState()
        setStreamingErrorMessage(
          error instanceof Error ? error.message : String(error)
        )
        if (ctx.newSessionId) {
          setSessionsData(
            (prevSessionsData) =>
              prevSessionsData?.filter(
                (session) => session.session_id !== ctx.newSessionId
              ) ?? null
          )
        }
      } finally {
        focusChatInput()
        setIsStreaming(false)
      }
    },
    [
      addMessage,
      agentId,
      authHeaders,
      focusChatInput,
      mode,
      processChunk,
      selectedEndpoint,
      sessionId,
      setIsStreaming,
      setMessages,
      setPendingApproval,
      setSessionsData,
      setStreamingErrorMessage,
      streamResponse,
      teamId,
      updateMessagesWithErrorState
    ]
  )

  /**
   * Answers the pending approval and resumes the run.
   *
   * `approved` false is not a cancel: the run continues with the tool refused,
   * so the agent gets to say what it will do instead. Cancelling would leave the
   * run parked on the server forever.
   */
  const handleApproval = useCallback(
    async (approved: boolean) => {
      if (!pendingApproval) return

      const {
        runId,
        sessionId: pausedSessionId,
        requirements
      } = pendingApproval
      const componentId = mode === 'team' ? teamId : agentId
      if (!componentId) {
        setStreamingErrorMessage('Please select an agent or team first.')
        return
      }

      setIsResolvingApproval(true)
      setIsStreaming(true)
      setPendingApproval(null)

      const ctx: StreamContext = {
        lastContent: '',
        newSessionId: pausedSessionId,
        sessionName: ''
      }

      try {
        const endpointUrl = constructEndpointUrl(selectedEndpoint)
        const continueUrl =
          mode === 'team'
            ? APIRoutes.TeamContinueRun(endpointUrl, componentId, runId)
            : APIRoutes.AgentContinueRun(endpointUrl, componentId, runId)

        // The server rebuilds each requirement from this object, so it goes back
        // whole with only `confirmation` filled in. Trimming it to the id would
        // lose the tool call it points at.
        const answered: RunRequirement[] = requirements.map((requirement) => ({
          ...requirement,
          confirmation: approved,
          confirmation_note: approved ? null : 'The user declined.'
        }))

        const formData = new FormData()
        formData.append('requirements', JSON.stringify(answered))
        formData.append('session_id', pausedSessionId)
        formData.append('stream', 'true')

        await streamResponse({
          apiUrl: continueUrl,
          headers: authHeaders(),
          requestBody: formData,
          onChunk: (chunk: RunResponse) => processChunk(chunk, ctx),
          onError: (error) => {
            updateMessagesWithErrorState()
            setStreamingErrorMessage(error.message)
          },
          onComplete: () => {}
        })
      } catch (error) {
        updateMessagesWithErrorState()
        setStreamingErrorMessage(
          error instanceof Error ? error.message : String(error)
        )
      } finally {
        setIsResolvingApproval(false)
        setIsStreaming(false)
        focusChatInput()
      }
    },
    [
      agentId,
      authHeaders,
      focusChatInput,
      mode,
      pendingApproval,
      processChunk,
      selectedEndpoint,
      setIsResolvingApproval,
      setIsStreaming,
      setPendingApproval,
      setStreamingErrorMessage,
      streamResponse,
      teamId,
      updateMessagesWithErrorState
    ]
  )

  return { handleStreamResponse, handleApproval }
}

export default useAIChatStreamHandler
