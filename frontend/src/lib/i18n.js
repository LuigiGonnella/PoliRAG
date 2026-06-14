export const LANGUAGES = {
  en: "English",
  it: "Italiano",
};

const STRINGS = {
  en: {
    about: "About",
    allCoursesInYear: "All courses in this year",
    assistantDescription:
      "Ask questions across your university notes, search course material faster, and narrow answers to a specific academic year or course when needed.",
    cancel: "Cancel",
    chatCount: "Chat count",
    chooseSearch: "Choose how Polyhedric should search",
    chooseYearFirst: "Choose a year first",
    closeChatHistory: "Close chat history",
    course: "Course",
    courseCatalogMissing: "Course catalog is not available right now. General chat still works.",
    currentScope: "Current scope",
    delete: "Delete",
    deleteChat: "Delete chat",
    deletePrompt: "This permanently deletes",
    deletePromptEnd: "and its saved messages.",
    deleting: "Deleting",
    email: "Email",
    general: "General",
    generalChat: "General chat",
    generalDescription: "Search across the available knowledge base without a course restriction.",
    generalKnowledgeBase: "General knowledge base",
    github: "GitHub",
    language: "Language",
    loadingChats: "Loading chats...",
    loadingYears: "Loading years...",
    menuCollapse: "Collapse chat history",
    menuOpen: "Open chat history",
    newChat: "New chat",
    noRecentChats: "No saved chats yet. Start a new chat when you are ready.",
    optional: "optional",
    portfolio: "Portfolio",
    previousChats: "Previous chats",
    recentChats: "Recent chats",
    removeConversation: "Remove this conversation?",
    scopeAllCourses: "all courses",
    scopedRetrieval: "Scoped retrieval",
    scopedRetrievalDescription: "Start general, choose a year, or focus on one course.",
    selectYear: "Select a year...",
    send: "Send",
    sending: "Sending",
    specific: "Specific",
    specificDescription: "Restrict retrieval to an academic year, with an optional course filter.",
    specificHelp: "Choose only a year to search all courses in that year, or add a course for a narrower chat.",
    startChat: "Start chat",
    starting: "Starting",
    studyAssistant: "RAG study assistant",
    textareaPlaceholder: "Ask about exams, definitions, proofs, labs, slides, or notes",
    thisChat: "this chat",
    untitledChat: "Untitled chat",
    userLabel: "You",
    year: "Academic year",
  },
  it: {
    about: "Info",
    allCoursesInYear: "Tutti i corsi di questo anno",
    assistantDescription:
      "Fai domande sui tuoi appunti universitari, cerca materiale piu rapidamente e restringi le risposte a un anno accademico o a un corso specifico.",
    cancel: "Annulla",
    chatCount: "Numero chat",
    chooseSearch: "Scegli come Polyhedric deve cercare",
    chooseYearFirst: "Scegli prima un anno",
    closeChatHistory: "Chiudi cronologia chat",
    course: "Corso",
    courseCatalogMissing: "Il catalogo corsi non e disponibile ora. La chat generale funziona comunque.",
    currentScope: "Ambito corrente",
    delete: "Elimina",
    deleteChat: "Elimina chat",
    deletePrompt: "Questo elimina definitivamente",
    deletePromptEnd: "e i messaggi salvati.",
    deleting: "Elimino",
    email: "Email",
    general: "Generale",
    generalChat: "Chat generale",
    generalDescription: "Cerca in tutta la base di conoscenza disponibile senza limitazioni di corso.",
    generalKnowledgeBase: "Base di conoscenza generale",
    github: "GitHub",
    language: "Lingua",
    loadingChats: "Caricamento chat...",
    loadingYears: "Caricamento anni...",
    menuCollapse: "Comprimi cronologia chat",
    menuOpen: "Apri cronologia chat",
    newChat: "Nuova chat",
    noRecentChats: "Non ci sono chat salvate. Inizia una nuova chat quando vuoi.",
    optional: "opzionale",
    portfolio: "Portfolio",
    previousChats: "Chat precedenti",
    recentChats: "Chat recenti",
    removeConversation: "Rimuovere questa conversazione?",
    scopeAllCourses: "tutti i corsi",
    scopedRetrieval: "Ricerca contestuale",
    scopedRetrievalDescription: "Inizia in generale, scegli un anno o concentrati su un corso.",
    selectYear: "Seleziona un anno...",
    send: "Invia",
    sending: "Invio",
    specific: "Specifica",
    specificDescription: "Limita la ricerca a un anno accademico, con filtro corso opzionale.",
    specificHelp: "Scegli solo un anno per cercare in tutti i corsi, oppure aggiungi un corso per restringere.",
    startChat: "Avvia chat",
    starting: "Avvio",
    studyAssistant: "Assistente RAG per lo studio",
    textareaPlaceholder: "Chiedi di esami, definizioni, dimostrazioni, laboratori, slide o appunti",
    thisChat: "questa chat",
    untitledChat: "Chat senza titolo",
    userLabel: "Tu",
    year: "Anno accademico",
  },
};

const DEGREE_LABELS = {
  Magistrale: { en: "Master", it: "Magistrale" },
  Triennale: { en: "Bachelor", it: "Triennale" },
};

const YEAR_LABELS = {
  "Primo Anno": { en: "First Year", it: "Primo Anno" },
  "Secondo Anno": { en: "Second Year", it: "Secondo Anno" },
  "Terzo Anno": { en: "Third Year", it: "Terzo Anno" },
};

const COURSE_LABELS = {
  "Algebra Lineare e Geometria": { en: "Linear Algebra and Geometry", it: "Algebra Lineare e Geometria" },
  Algoritmi: { en: "Algorithms", it: "Algoritmi" },
  Analisi: { en: "Mathematical Analysis", it: "Analisi" },
  "Analisi 2": { en: "Mathematical Analysis 2", it: "Analisi 2" },
  "Applicazioni Web I": { en: "Web Applications I", it: "Applicazioni Web I" },
  "Architetture dei Sistemi di Elaborazione": {
    en: "Computer Systems Architecture",
    it: "Architetture dei Sistemi di Elaborazione",
  },
  "Basi di Dati": { en: "Databases", it: "Basi di Dati" },
  Benessere: { en: "Wellbeing", it: "Benessere" },
  "Calcolatori Elettronici": { en: "Computer Architecture", it: "Calcolatori Elettronici" },
  Chimica: { en: "Chemistry", it: "Chimica" },
  "COLLABORAZIONI PART-TIME": { en: "Part-Time Collaborations", it: "Collaborazioni part-time" },
  "Controlli Automatici": { en: "Automatic Control", it: "Controlli Automatici" },
  "Elettronica Applicata": { en: "Applied Electronics", it: "Elettronica Applicata" },
  Elettrotecnica: { en: "Electrical Engineering", it: "Elettrotecnica" },
  "Fisica I": { en: "Physics I", it: "Fisica I" },
  "Fisica 2": { en: "Physics 2", it: "Fisica 2" },
  Informatica: { en: "Computer Science", it: "Informatica" },
  "MachineLearning_for_Vision_and_Multimedia": {
    en: "Machine Learning for Vision and Multimedia",
    it: "Machine Learning for Vision and Multimedia",
  },
  Metodi: { en: "Methods", it: "Metodi" },
  ML_In_Applications: { en: "Machine Learning in Applications", it: "Machine Learning in Applications" },
  "Programmazione Oggetti": { en: "Object-Oriented Programming", it: "Programmazione a Oggetti" },
  "Programmazione Sistema": { en: "Systems Programming", it: "Programmazione di Sistema" },
  Reti: { en: "Networks", it: "Reti" },
  Segnali: { en: "Signals", it: "Segnali" },
  "Sicurezza_Sistemi_Informativi": {
    en: "Information Systems Security",
    it: "Sicurezza dei Sistemi Informativi",
  },
  "Sistemi Elettronici, Tecnologie e Misure": {
    en: "Electronic Systems, Technologies and Measurements",
    it: "Sistemi Elettronici, Tecnologie e Misure",
  },
  "Sistemi Operativi": { en: "Operating Systems", it: "Sistemi Operativi" },
  "Software_Engineering_2": { en: "Software Engineering 2", it: "Software Engineering 2" },
  "Tecniche di Programmazione": { en: "Programming Techniques", it: "Tecniche di Programmazione" },
  "Tecnologie e Servizi di Rete": { en: "Network Technologies and Services", it: "Tecnologie e Servizi di Rete" },
};

export function t(key, language = "en") {
  return STRINGS[language]?.[key] || STRINGS.en[key] || key;
}

export function degreeLabel(value, language = "en") {
  return DEGREE_LABELS[value]?.[language] || value || "";
}

export function yearLabel(value, language = "en") {
  return YEAR_LABELS[value]?.[language] || value || "";
}

export function courseLabel(course, language = "en") {
  const value = typeof course === "string" ? course : course?.value || course?.label || "";
  const fallback = typeof course === "string" ? course : course?.label || value;
  return COURSE_LABELS[value]?.[language] || COURSE_LABELS[fallback]?.[language] || cleanCourseLabel(fallback);
}

export function groupLabel(group, language = "en") {
  if (!group) return "";
  return `${degreeLabel(group.degree.value, language)} / ${yearLabel(group.year.value, language)}`;
}

export function sessionTitle(session, language = "en") {
  if (!session) return "";
  if (session.title === "General chat") return t("generalChat", language);
  if (session.course_filter) return courseLabel(session.course_filter, language);
  return session.title || t("untitledChat", language);
}

function cleanCourseLabel(value) {
  return String(value || "").replaceAll("_", " ");
}
