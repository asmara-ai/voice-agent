import { useState } from "react";
import { CloudLightning, CloudOff, MessageSquare } from "react-feather";
import Button from "./Button";

// Remove sessionUpdate from here since it will be handled in the backend
export default function SessionControls({
  startSession,
  stopSession,
  sendTextMessage,
  isSessionActive,
  isActivating,
  setIsActivating,
  sendClientEvent,
}) {
  function SessionStopped({ startSession }) {
    async function handleStartSession() {
      if (isActivating) return;
      setIsActivating(true);
      await startSession();
    }

    return (
      <div className="flex items-center justify-center w-full h-full">
        <Button
          onClick={handleStartSession}
          disabled={isActivating}
          className={isActivating ? "bg-gray-500" : "bg-black"}
          icon={<CloudLightning height={16} />}
        >
          {isActivating ? "starting session..." : "start session"}
        </Button>
      </div>
    );
  }

  function SessionActive({ stopSession, sendTextMessage }) {
    const [message, setMessage] = useState("");

    function handleSendClientEvent() {
      if (message.trim()) {
        sendTextMessage(message);
        setMessage("");
      }
    }

    return (
      <div className="flex items-center justify-center w-full h-full gap-4">
         {/* <input
        onKeyDown={(e) => {
          if (e.key === "Enter" && message.trim()) {
            handleSendClientEvent();
          }
        }}
        type="text"
        placeholder="send a text message..."
        className="border border-gray-200 rounded-full p-4 flex-1"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <Button
        onClick={() => {
          if (message.trim()) {
            handleSendClientEvent();
          }
        }}
        icon={<MessageSquare height={16} />}
        className="bg-blue-400"
      >
        send text
      </Button> */}
        <Button onClick={stopSession} icon={<CloudOff height={16} />}>
          disconnect
        </Button>
      </div>
    );
  }

  return (
    <div className="flex gap-4 border-t-2 border-gray-200 h-full rounded-md">
      {isSessionActive ? (
        <SessionActive
          stopSession={stopSession}
          sendTextMessage={sendTextMessage}
        />
      ) : (
        <SessionStopped startSession={startSession} />
      )}
    </div>
  );
}
