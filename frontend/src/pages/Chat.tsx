import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bug,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  MessageSquare,
  Settings,
  ThumbsDown,
  ThumbsUp,
  UserCircle,
  X,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import MusicbotLogo from '@/components/MusicbotLogo';

type MessageRole = 'user' | 'bot';
type ConversationRating = 'positive' | 'negative' | null;

interface Source {
  name: string;
  category: string;
  origin: string;
  date: string;
  version: string;
  excerpt: string;
}

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  sources?: Source[];
}

interface Conversation {
  id: string;
  title: string;
  updatedAt: string;
  messages: Message[];
}

const DEFAULT_BOT_REPLY =
  'No momento não foi possível gerar uma resposta. Tente novamente mais tarde.';

const Chat = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [conversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [conversationRating, setConversationRating] = useState<ConversationRating>(null);

  const [showHistory, setShowHistory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);

  const [feedbackText, setFeedbackText] = useState('');
  const [preferences, setPreferences] = useState({
    audioEnabled: true,
    compactMode: false,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resizeTextarea = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  };

  const displayName = useMemo(() => {
    if (!user?.name) return 'Visitante';
    return user.name.split(' ')[0];
  }, [user?.name]);

  const currentConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === currentConversationId) ?? null,
    [conversations, currentConversationId],
  );

  const conversationTitle = currentConversation?.title ?? 'Nova conversa';
  const canNavigateConversations = conversations.length > 0;

  useEffect(() => {
    const timer = globalThis.setTimeout(() => setHistoryLoading(false), 800);
    return () => globalThis.clearTimeout(timer);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    resizeTextarea();
  }, [inputValue]);

  const openDashboard = () => {
    setShowSettings(false);
    navigate('/dashboard');
  };

  const openKnowledgeBase = () => {
    setShowSettings(false);
    navigate('/base-conhecimento');
  };

  const openProfile = () => {
    setShowSettings(false);
    navigate('/profile');
  };

  const handleLogout = () => {
    setShowSettings(false);
    logout();
    navigate('/login');
  };

  const handleSendMessage = () => {
    const text = inputValue.trim();
    if (!text) return;

    const now = new Date().toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    });

    const userMessage: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: now,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsTyping(true);

    globalThis.setTimeout(() => {
      const botMessage: Message = {
        id: `b-${Date.now()}`,
        role: 'bot',
        content: DEFAULT_BOT_REPLY,
        timestamp: new Date().toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit',
        }),
      };

      setMessages((prev) => [...prev, botMessage]);
      setIsTyping(false);
    }, 700);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    handleSendMessage();
  };

  const handlePreviousConversation = () => {
    if (!canNavigateConversations) return;

    const currentIndex = conversations.findIndex((item) => item.id === currentConversationId);
    const nextIndex = currentIndex <= 0 ? conversations.length - 1 : currentIndex - 1;
    setCurrentConversationId(conversations[nextIndex].id);
    setMessages(conversations[nextIndex].messages);
  };

  const handleNextConversation = () => {
    if (!canNavigateConversations) return;

    const currentIndex = conversations.findIndex((item) => item.id === currentConversationId);
    const nextIndex = currentIndex >= conversations.length - 1 ? 0 : currentIndex + 1;
    setCurrentConversationId(conversations[nextIndex].id);
    setMessages(conversations[nextIndex].messages);
  };

  const handleSelectConversation = (id: string) => {
    const selected = conversations.find((conversation) => conversation.id === id);
    if (!selected) return;

    setCurrentConversationId(selected.id);
    setMessages(selected.messages);
    setShowHistory(false);
  };

  const handleNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
    setConversationRating(null);
    setShowHistory(false);
  };

  const userAvatar = user?.avatar || 'https://api.dicebear.com/7.x/initials/svg?seed=visitante';
  const userAlt = user?.name || 'Usuário visitante';

  let historyContent: JSX.Element;
  if (historyLoading) {
    historyContent = (
      <div className="space-y-2">
        <div className="h-12 rounded-xl bg-white/10 animate-pulse" />
        <div className="h-12 rounded-xl bg-white/10 animate-pulse" />
        <div className="h-12 rounded-xl bg-white/10 animate-pulse" />
      </div>
    );
  } else if (conversations.length === 0) {
    historyContent = <p className="text-slate text-sm py-4">Dados nao encontrados.</p>;
  } else {
    historyContent = (
      <div className="space-y-2 max-h-64 overflow-auto">
        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            type="button"
            onClick={() => handleSelectConversation(conversation.id)}
            className={`w-full text-left rounded-xl px-3 py-3 transition-colors ${
              conversation.id === currentConversationId
                ? 'bg-white/15 text-off-white'
                : 'bg-white/5 text-slate hover:text-off-white hover:bg-white/10'
            }`}
          >
            <p className="text-sm font-medium truncate">{conversation.title}</p>
            <p className="text-xs mt-0.5">{conversation.updatedAt}</p>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-midnight flex flex-col">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 pt-5 sm:pt-6 pb-5">
        <div className="flex justify-center mb-5 sm:mb-6">
          <MusicbotLogo size="sm" />
        </div>

        <div className="flex-1 overflow-y-auto min-h-0 space-y-4 sm:space-y-5 pb-5 sm:pb-6 pr-1">
          {messages.length === 0 ? (
            <div className="glass rounded-2xl p-6 sm:p-8 text-center max-w-2xl mx-auto">
              <h2 className="font-display text-xl text-off-white mb-2">Bem-vindo, {displayName}</h2>
              <p className="text-slate text-sm sm:text-base">Dados nao encontrados para esta conversa.</p>
              <p className="text-slate text-sm mt-2">
                Envie uma mensagem para iniciar um novo contexto enquanto a integracao com backend nao esta disponivel.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <article
                key={message.id}
                className={`w-full flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[90%] sm:max-w-[78%] rounded-2xl px-4 sm:px-5 py-3 sm:py-4 ${
                    message.role === 'user'
                      ? 'bg-teal text-off-white rounded-br-md'
                      : 'glass text-off-white rounded-bl-md'
                  }`}
                >
                  <p className="text-sm sm:text-base whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  <div className="mt-2 text-xs text-slate flex items-center gap-2">
                    <span>{message.timestamp}</span>
                    {message.sources && message.sources.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setSelectedSource(message.sources?.[0] ?? null)}
                        className="text-teal hover:underline"
                      >
                        Fonte
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))
          )}

          {isTyping && (
            <div className="flex items-center gap-1 glass rounded-2xl rounded-bl-md px-4 py-3 w-fit">
              <div className="w-2 h-2 rounded-full bg-teal typing-dot" />
              <div className="w-2 h-2 rounded-full bg-teal typing-dot" />
              <div className="w-2 h-2 rounded-full bg-teal typing-dot" />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="glass rounded-2xl px-3 py-3 sm:px-4 sm:py-4">
          <div className="flex items-end gap-3 sm:gap-4">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              placeholder="Digite sua mensagem..."
              rows={1}
              className="w-full min-h-[44px] resize-none overflow-y-auto bg-transparent text-off-white placeholder:text-slate focus:outline-none text-sm sm:text-base leading-6 max-h-40"
            />
            <button
              type="submit"
              className="shrink-0 h-11 bg-magenta text-off-white rounded-xl px-5 text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-50"
              disabled={!inputValue.trim()}
            >
              Enviar
            </button>
          </div>
        </form>

        <div className="grid grid-cols-[1fr_auto_1fr] items-center mt-4 sm:mt-5 px-1 gap-3">
          <div className="flex items-center gap-1 sm:gap-2 justify-self-start">
            <button
              type="button"
              onClick={() => setConversationRating(conversationRating === 'positive' ? null : 'positive')}
              title="Conversa satisfatoria"
              className={`p-2 rounded-lg transition-all duration-200 ${
                conversationRating === 'positive'
                  ? 'bg-[hsla(170,71%,41%,0.2)] text-teal'
                  : 'text-slate hover:text-off-white'
              }`}
            >
              <ThumbsUp size={18} />
            </button>
            <button
              type="button"
              onClick={() => setConversationRating(conversationRating === 'negative' ? null : 'negative')}
              title="Conversa insatisfatoria"
              className={`p-2 rounded-lg transition-all duration-200 ${
                conversationRating === 'negative'
                  ? 'bg-[hsla(342,74%,57%,0.2)] text-magenta'
                  : 'text-slate hover:text-off-white'
              }`}
            >
              <ThumbsDown size={18} />
            </button>
            <button
              type="button"
              onClick={() => setShowFeedback(true)}
              title="Relatar problema"
              className="p-2 rounded-lg text-slate hover:text-off-white transition-colors duration-200"
            >
              <Bug size={18} />
            </button>
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowExportMenu((prev) => !prev)}
                title="Exportar conversa"
                className="p-2 rounded-lg text-slate hover:text-off-white transition-colors duration-200"
              >
                <Download size={18} />
              </button>
              {showExportMenu && (
                <div className="absolute left-0 bottom-11 glass rounded-xl p-2 w-48 z-20">
                  <p className="text-xs text-slate px-2 py-1">Exportacao (em breve)</p>
                  {['PDF', 'TXT', 'JSON'].map((format) => (
                    <button
                      key={format}
                      type="button"
                      disabled
                      className="w-full text-left px-2 py-2 rounded-lg text-off-white/70 text-sm cursor-not-allowed"
                    >
                      Exportar como {format}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 min-w-0 justify-self-center">
            <button
              type="button"
              onClick={handlePreviousConversation}
              disabled={!canNavigateConversations}
              className="p-1 text-slate hover:text-off-white transition-colors disabled:opacity-30"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              type="button"
              onClick={() => setShowHistory(true)}
              className="text-slate text-sm hover:text-off-white transition-colors font-body max-w-[220px] truncate text-center"
            >
              {conversationTitle}
            </button>
            <button
              type="button"
              onClick={handleNextConversation}
              disabled={!canNavigateConversations}
              className="p-1 text-slate hover:text-off-white transition-colors disabled:opacity-30"
            >
              <ChevronRight size={18} />
            </button>
          </div>

          <div className="relative justify-self-end">
            <button type="button" onClick={() => setShowSettings((prev) => !prev)} className="relative">
              <img
                src={userAvatar}
                alt={userAlt}
                className="w-9 h-9 rounded-full border-2 border-teal hover:scale-105 transition-transform duration-200"
              />
            </button>

            {showSettings && (
              <div className="absolute right-0 bottom-12 glass rounded-xl p-2 w-64 z-20">
                <button
                  type="button"
                  onClick={openDashboard}
                  className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-off-white"
                >
                  Dashboard
                  <ExternalLink size={15} className="text-slate" />
                </button>
                <button
                  type="button"
                  onClick={openKnowledgeBase}
                  className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-off-white"
                >
                  Base de conhecimento
                  <ExternalLink size={15} className="text-slate" />
                </button>
                <button
                  type="button"
                  onClick={openProfile}
                  className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-off-white"
                >
                  Perfil
                  <UserCircle size={15} className="text-slate" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowSettings(false);
                    setShowPreferences(true);
                  }}
                  className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-off-white"
                >
                  Preferencias
                  <Settings size={15} className="text-slate" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowSettings(false);
                    setShowFeedback(true);
                  }}
                  className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-off-white"
                >
                  Feedback
                  <MessageSquare size={15} className="text-slate" />
                </button>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-magenta"
                >
                  Sair
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {showHistory && (
        <div className="fixed inset-0 bg-black/50 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="glass rounded-2xl w-full max-w-lg p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Historico de conversas</h3>
              <button type="button" onClick={() => setShowHistory(false)} className="text-slate hover:text-off-white">
                <X size={18} />
              </button>
            </div>

            {historyContent}

            <button
              type="button"
              onClick={handleNewConversation}
              className="mt-4 w-full bg-magenta text-off-white rounded-xl py-2.5 text-sm font-semibold hover:brightness-110"
            >
              Nova conversa
            </button>
          </div>
        </div>
      )}

      {showFeedback && (
        <div className="fixed inset-0 bg-black/50 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="glass rounded-2xl w-full max-w-lg p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Enviar feedback</h3>
              <button type="button" onClick={() => setShowFeedback(false)} className="text-slate hover:text-off-white">
                <X size={18} />
              </button>
            </div>
            <textarea
              value={feedbackText}
              onChange={(event) => setFeedbackText(event.target.value)}
              placeholder="Descreva seu feedback..."
              className="w-full h-28 rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-sm text-off-white placeholder:text-slate focus:outline-none"
            />
            <button
              type="button"
              onClick={() => {
                setFeedbackText('');
                setShowFeedback(false);
              }}
              className="mt-4 w-full bg-teal text-off-white rounded-xl py-2.5 text-sm font-semibold hover:brightness-110"
            >
              Enviar (sem integracao)
            </button>
          </div>
        </div>
      )}

      {showPreferences && (
        <div className="fixed inset-0 bg-black/50 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="glass rounded-2xl w-full max-w-md p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Preferencias</h3>
              <button
                type="button"
                onClick={() => setShowPreferences(false)}
                className="text-slate hover:text-off-white"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3">
              <label className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-3">
                <span className="text-sm text-off-white">Habilitar audio</span>
                <input
                  type="checkbox"
                  checked={preferences.audioEnabled}
                  onChange={(event) =>
                    setPreferences((prev) => ({
                      ...prev,
                      audioEnabled: event.target.checked,
                    }))
                  }
                />
              </label>
              <label className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-3">
                <span className="text-sm text-off-white">Modo compacto</span>
                <input
                  type="checkbox"
                  checked={preferences.compactMode}
                  onChange={(event) =>
                    setPreferences((prev) => ({
                      ...prev,
                      compactMode: event.target.checked,
                    }))
                  }
                />
              </label>
            </div>
          </div>
        </div>
      )}

      {selectedSource && (
        <div className="fixed inset-0 bg-black/50 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="glass rounded-2xl w-full max-w-xl p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Fonte</h3>
              <button type="button" onClick={() => setSelectedSource(null)} className="text-slate hover:text-off-white">
                <X size={18} />
              </button>
            </div>
            <p className="text-off-white text-sm font-semibold">{selectedSource.name}</p>
            <p className="text-slate text-sm mt-1">
              {selectedSource.category} | {selectedSource.origin} | {selectedSource.date} | {selectedSource.version}
            </p>
            <p className="text-off-white text-sm mt-3 leading-relaxed">{selectedSource.excerpt}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
