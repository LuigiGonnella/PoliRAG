import { ChatPage } from "./pages/ChatPage.jsx";
import { useChatController } from "./hooks/useChatController.js";

export default function App() {
  const controller = useChatController();
  return <ChatPage controller={controller} />;
}
