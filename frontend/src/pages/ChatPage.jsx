import { AboutModal } from "../components/AboutModal.jsx";
import { ChatWindow } from "../components/ChatWindow.jsx";
import { DeleteChatModal } from "../components/DeleteChatModal.jsx";
import { NewChatModal } from "../components/NewChatModal.jsx";
import { Sidebar } from "../components/Sidebar.jsx";
import { Topbar } from "../components/Topbar.jsx";

export function ChatPage({ controller }) {
  const { state, actions } = controller;
  const shellClass = [
    "app-shell",
    state.sidebarCollapsed ? "sidebar-collapsed" : "",
    state.mobileSidebarOpen ? "sidebar-open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <>
      <div className={shellClass}>
        <Sidebar state={state} actions={actions} />
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close chat history"
          onClick={actions.closeMobileSidebar}
        />

        <main className="workspace">
          <Topbar state={state} actions={actions} />
          <ChatWindow state={state} actions={actions} />
        </main>
      </div>

      <NewChatModal state={state} actions={actions} />
      <DeleteChatModal state={state} actions={actions} />
      <AboutModal language={state.language} open={state.modal === "about"} onClose={() => actions.setModal(null)} />
    </>
  );
}
