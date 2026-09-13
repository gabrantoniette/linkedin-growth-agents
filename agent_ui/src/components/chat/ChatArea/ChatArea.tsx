'use client'

import ApprovalRequest from './ApprovalRequest'
import ChatInput from './ChatInput'
import MessageArea from './MessageArea'
const ChatArea = () => {
  return (
    <main className="relative m-1.5 flex flex-grow flex-col rounded-xl bg-background">
      <MessageArea />
      {/* Above the input, inside the sticky block: a paused run blocks the
          conversation, so the question has to be where the user is already
          looking and cannot be scrolled away from. */}
      <div className="sticky bottom-0 ml-9 px-4 pb-2">
        <ApprovalRequest />
        <ChatInput />
      </div>
    </main>
  )
}

export default ChatArea
