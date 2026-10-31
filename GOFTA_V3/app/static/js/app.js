(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const app = $("#app");
  const csrf = $('meta[name="csrf-token"]').content;
  const state = { me: null, conversations: [], active: null, filter: "all", socket: null, file: null, members: [], lastMessageId: 0, pollError: null, userSearchQuery: "", userSearchResults: null, userSearchSequence: 0, userSearchTimer: null };
  const translations = {
    fa: { all: "همه", unread: "خوانده‌نشده", direct: "شخصی", group: "گروه‌ها", channel: "کانال‌ها", bot: "ربات‌ها", saved: "ذخیره‌شده", online: "آنلاین", member: "عضو", members: "عضو", send: "ارسال", noMessages: "هنوز پیامی نیست.", save: "ذخیره", savedDone: "ذخیره شد", profile: "ویرایش پروفایل", language: "زبان", theme: "پوسته", light: "روشن", dark: "تاریک", search: "جست‌وجو در گفتگوها", emptyTitle: "گفت‌وگوی شما، همین‌جاست", emptyBody: "یک گفتگو از فهرست انتخاب کنید یا گفت‌وگوی تازه‌ای بسازید.", newChat: "شروع گفت‌وگوی تازه", writeMessage: "پیامی بنویسید…", allChats: "همه", createChat: "گفت‌وگوی تازه", type: "نوع گفتگو", username: "نام کاربری", title: "نام گفتگو", addMembers: "افزودن اعضا", create: "ایجاد گفتگو", membersTitle: "اعضای گفتگو", profileName: "نام نمایشی", bio: "توضیحات", chatNone: "گفتگویی برای نمایش نیست.", botNone: "رباتی در این نسخه اضافه نشده است.", savedPreview: "پیام‌های ذخیره‌شده", saveProfile: "ذخیرهٔ پروفایل", picture: "عکس نمایه", deletePicture: "حذف تصویر", signOut: "خروج از حساب", addMember: "افزودن عضو", makeAdmin: "مدیر", makeMember: "عضو", remove: "حذف", savedToast: "پیام ذخیره شد.", unsavedToast: "از ذخیره‌شده‌ها برداشته شد.", addedToast: "عضو اضافه شد.", owner: "سازنده", admin: "مدیر", roleMember: "عضو", download: "دانلود",     menu: "منو", editProfile: "ویرایش پروفایل", newChannel: "ایجاد کانال" },
    en: { all: "All", unread: "Unread", direct: "Personal", group: "Groups", channel: "Channels", bot: "Bots", saved: "Saved", online: "Online", member: "member", members: "members", send: "Send", noMessages: "No messages yet.", save: "Save", savedDone: "Saved", profile: "Edit profile", language: "Language", theme: "Theme", light: "Light", dark: "Dark", search: "Search chats", emptyTitle: "Your conversations, all in one place", emptyBody: "Choose a conversation or start a new one.", newChat: "Start a new chat", writeMessage: "Write a message…", allChats: "All", createChat: "New conversation", type: "Conversation type", username: "Username", title: "Conversation name", addMembers: "Add members", create: "Create conversation", membersTitle: "Conversation members", profileName: "Display name", bio: "About you", chatNone: "No conversations to show.", botNone: "No bots are configured in this version.", savedPreview: "Saved messages", saveProfile: "Save profile", picture: "Profile picture", deletePicture: "Remove picture", signOut: "Sign out", addMember: "Add member", makeAdmin: "Make admin", makeMember: "Make member", remove: "Remove", savedToast: "Message saved.", unsavedToast: "Removed from saved messages.", addedToast: "Member added.", owner: "Owner", admin: "Admin", roleMember: "Member", download: "Download",     menu: "Menu", editProfile: "Edit profile", newChannel: "Create channel" }
  };
  Object.assign(translations.fa, {
    font: "فونت فارسی", vazirmatn: "وزیرمتن", systemFont: "فونت پیش‌فرض دستگاه",
    colorTheme: "رنگ تم", blue: "آبی", violet: "بنفش", green: "سبز",
    rose: "صورتی", amber: "کهربایی", teal: "فیروزه‌ای",
    settings: "تنظیمات", contacts: "مخاطبین", searchContacts: "جست‌وجوی نام یا نام کاربری",
    contactsHint: "برای پیدا کردن و شروع گفتگو، نام مخاطب را جست‌وجو کنید.",
    noContacts: "مخاطبی پیدا نشد.", newChannel: "ایجاد کانال",
    myProfile: "پروفایل من", newGroup: "ایجاد گروه", nightMode: "حالت شب",
    savedMessages: "پیام‌های ذخیره‌شده", menuLabel: "منوی اصلی",
    phone: "شماره تلفن", phoneVisibility: "چه کسانی شماره را ببینند؟",
    phonePrivate: "فقط خودم", phoneMembers: "اعضای گفتگوهایم", phonePublic: "همه",
    sendCode: "ارسال کد تأیید", verifyPhone: "تأیید شماره", removePhone: "حذف شماره",
    phoneVerified: "شماره تأیید شده است.", phonePending: "شماره هنوز تأیید نشده است.",
    enterCode: "کد شش‌رقمی", codeSent: "کد آزمایشی", phoneSaved: "شماره با موفقیت تأیید شد.",
    phoneRemoved: "شماره حذف شد.", phoneHint: "برای ورود با شماره، آن را با کد پیامکی تأیید کنید.",
    contactsNone: "هنوز مخاطبی اضافه نکرده‌اید.", addContact: "افزودن مخاطب",
    contactAdded: "مخاطب اضافه شد.", lastSeen: "آخرین بازدید", sortContacts: "مرتب‌سازی مخاطبین",
    offline: "غیرفعال",
    fileManager: "مدیریت فایل‌ها", fileUsage: "حجم فایل‌های در دسترس شما",
    noFiles: "فایلی برای نمایش نیست.", deleteFile: "حذف فایل",
    deleteFileConfirm: "این فایل را برای همهٔ اعضای گفتگو حذف می‌کنید؟",
    directConversation: "گفتگوی خصوصی",
    searchPeople: "افراد", searchingPeople: "در حال جست‌وجوی افراد…",
    noSearchResults: "گفتگو یا فردی پیدا نشد.", startConversation: "شروع گفتگوی خصوصی",
    notifications: "اعلان پیام‌های جدید", allowNotifications: "اجازه اعلان‌های مرورگر",
    notificationsAllowed: "اعلان‌های مرورگر فعال شد.", notificationsDenied: "اجازه اعلان در تنظیمات مرورگر داده نشد.",
    notificationsUnsupported: "این مرورگر از اعلان دسکتاپ پشتیبانی نمی‌کند.",
    newMessage: "پیام جدید", removedFromConversation: "شما از این گفتگو حذف شدید.",
    removeMemberConfirm: "این عضو از گفتگو حذف شود؟",
  });
  Object.assign(translations.en, {
    font: "Persian font", vazirmatn: "Vazirmatn", systemFont: "System default",
    colorTheme: "Accent color", blue: "Blue", violet: "Violet", green: "Green",
    rose: "Rose", amber: "Amber", teal: "Teal",
    settings: "Settings", contacts: "Contacts", searchContacts: "Search name or username",
    contactsHint: "Search for a contact to find them and start a conversation.",
    noContacts: "No contacts found.", newChannel: "Create channel",
    myProfile: "My Profile", newGroup: "New Group", nightMode: "Night Mode",
    savedMessages: "Saved Messages", menuLabel: "Main menu",
    phone: "Phone number", phoneVisibility: "Who can see your phone?",
    phonePrivate: "Only me", phoneMembers: "Conversation members", phonePublic: "Everyone",
    sendCode: "Send verification code", verifyPhone: "Verify number", removePhone: "Remove number",
    phoneVerified: "Phone number verified.", phonePending: "Phone number is not verified.",
    enterCode: "Six-digit code", codeSent: "Test code", phoneSaved: "Phone number verified.",
    phoneRemoved: "Phone number removed.", phoneHint: "Verify it with an SMS code to sign in by phone.",
    contactsNone: "You have not added any contacts yet.", addContact: "Add Contact",
    contactAdded: "Contact added.", lastSeen: "Last seen", sortContacts: "Sort contacts",
    offline: "Offline",
    fileManager: "File management", fileUsage: "Accessible file storage",
    noFiles: "No files to show.", deleteFile: "Delete file",
    deleteFileConfirm: "Delete this file for everyone in the conversation?",
    directConversation: "Private conversation",
    searchPeople: "People", searchingPeople: "Searching people…",
    noSearchResults: "No conversations or people found.", startConversation: "Start private conversation",
    notifications: "New message notifications", allowNotifications: "Allow browser notifications",
    notificationsAllowed: "Browser notifications are enabled.", notificationsDenied: "Allow notifications in browser settings.",
    notificationsUnsupported: "This browser does not support desktop notifications.",
    newMessage: "New message", removedFromConversation: "You were removed from this conversation.",
    removeMemberConfirm: "Remove this member from the conversation?",
  });
  const palettes = {
    blue: ["#4b88e8", "#3678df", "#eaf1ff", "#263b57"],
    violet: ["#805ad5", "#6941c6", "#f0eafe", "#392c59"],
    green: ["#26966f", "#187a59", "#e3f5ed", "#214d40"],
    rose: ["#d95779", "#bf3e61", "#fbe8ee", "#59303e"],
    amber: ["#d28a16", "#b36b08", "#fff2d6", "#554322"],
    teal: ["#168f9b", "#087783", "#e0f5f5", "#204b50"],
  };
  const t = key => (translations[state.me?.language || "fa"][key] || key);

  function applyAppearance(settings) {
    const palette = palettes[settings.color_theme] || palettes.blue;
    document.body.dataset.theme = settings.theme || "light";
    document.documentElement.dataset.persianFont = settings.font_family || "vazirmatn";
    document.documentElement.style.setProperty("--accent", palette[0]);
    document.documentElement.style.setProperty("--accent-dark", palette[1]);
    document.documentElement.style.setProperty("--accent-soft", settings.theme === "dark" ? palette[3] : palette[2]);
  }
  function updateNightModeSwitch() {
    const enabled = state.me?.theme === "dark";
    const control = $("#menu-night-mode");
    if (!control) return;
    control.setAttribute("aria-checked", String(Boolean(enabled)));
    control.setAttribute("aria-label", t("nightMode"));
  }

  async function api(url, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set("X-CSRF-Token", csrf);
    if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
    const response = await fetch(url, { ...options, headers, credentials: "same-origin" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "درخواست انجام نشد.");
    return data;
  }
  function toast(message) {
    const node = document.createElement("div"); node.className = "toast"; node.textContent = message;
    $("#toast-region").append(node); setTimeout(() => node.remove(), 3400);
  }
  function imageAvatar(avatar, name, className = "avatar") {
    const span = document.createElement("span"); span.className = className; span.textContent = (name || "?").trim().slice(0, 1);
    if (avatar) { const image = new Image(); image.src = avatar; image.alt = ""; span.textContent = ""; span.append(image); }
    return span;
  }
  function showModal(title, content, variant = "") {
    $("#modal-title").textContent = title;
    const target = $("#modal-content"); target.replaceChildren(); target.append(content);
    const backdrop = $("#modal-backdrop");
    backdrop.classList.toggle("profile-sheet", variant === "profile-sheet");
    backdrop.classList.toggle("contacts-sheet", variant === "contacts-sheet");
    backdrop.classList.remove("hidden");
  }
  function closeModal() {
    const backdrop = $("#modal-backdrop");
    backdrop.classList.add("hidden");
    backdrop.classList.remove("profile-sheet", "contacts-sheet");
    if (state.me) applyAppearance(state.me);
  }
  function node(tag, className, text) {
    const item = document.createElement(tag); if (className) item.className = className; if (text !== undefined) item.textContent = text; return item;
  }
  function renderChats() {
    const list = $("#chat-list"); list.replaceChildren();
    const query = $("#chat-search").value.trim().toLocaleLowerCase();
    const items = state.filter === "saved" ? [{ id: "saved", title: t("saved"), kind: "saved", preview: "پیام‌های ذخیره‌شده", unread: 0 }] : state.conversations.filter(c => {
      if (state.filter === "unread" && !c.unread) return false;
      if (["direct", "group", "channel"].includes(state.filter) && c.kind !== state.filter) return false;
      if (state.filter === "bot") return false;
      return true;
    });
    const visible = items.filter(c => `${c.title} ${c.preview}`.toLocaleLowerCase().includes(query));
    if (!visible.length && (!query || query.length < 2 || state.filter === "saved" || state.filter === "bot")) {
      list.append(node("p", "muted", state.filter === "bot" ? t("botNone") : query ? t("noSearchResults") : t("chatNone")));
    }
    visible.forEach(c => {
      if (c.kind === "saved") c.preview = t("savedPreview");
      const button = node("button", `chat-row${state.active?.id === c.id ? " active" : ""}`);
      button.append(imageAvatar(c.avatar, c.title));
      const copy = node("span", "chat-copy"), top = node("span", "chat-top"), bottom = node("span", "chat-bottom");
      top.append(node("strong", "", c.title), node("span", "chat-time", c.latest_at ? new Date(c.latest_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""));
      bottom.append(node("span", "chat-preview", c.preview || (c.kind === "channel" ? "کانال" : "")));
      if (c.unread) bottom.append(node("span", "unread-count", String(c.unread)));
      copy.append(top, bottom); button.append(copy);
      button.addEventListener("click", () => c.kind === "saved" ? openSaved() : openConversation(c.id));
      list.append(button);
    });
    if (query.length < 2 || state.filter === "saved" || state.filter === "bot") {
      if (state.userSearchQuery) {
        state.userSearchQuery = "";
        state.userSearchResults = null;
        state.userSearchSequence += 1;
        clearTimeout(state.userSearchTimer);
      }
      return;
    }

    const section = node("p", "search-section-title", t("searchPeople"));
    list.append(section);
    if (state.userSearchQuery !== query) {
      state.userSearchQuery = query;
      state.userSearchResults = null;
      const sequence = ++state.userSearchSequence;
      clearTimeout(state.userSearchTimer);
      list.append(node("p", "muted search-status", t("searchingPeople")));
      state.userSearchTimer = setTimeout(async () => {
        try {
          const response = await api(`/api/users?q=${encodeURIComponent(query)}`);
          if (sequence !== state.userSearchSequence || state.userSearchQuery !== query) return;
          state.userSearchResults = response.users;
          renderChats();
        } catch (error) {
          if (sequence !== state.userSearchSequence) return;
          state.userSearchResults = [];
          toast(error.message);
          renderChats();
        }
      }, 250);
      return;
    }
    if (state.userSearchResults === null) {
      list.append(node("p", "muted search-status", t("searchingPeople")));
      return;
    }
    if (!state.userSearchResults.length && !visible.length) {
      section.textContent = t("noSearchResults");
      return;
    }
    state.userSearchResults.forEach(user => {
      const button = node("button", "chat-row user-search-row");
      button.type = "button";
      button.title = t("startConversation");
      button.append(imageAvatar(user.avatar, user.display_name));
      const copy = node("span", "chat-copy"), top = node("span", "chat-top"), bottom = node("span", "chat-bottom");
      top.append(node("strong", "", user.display_name));
      bottom.append(node("span", "chat-preview", `@${user.username}`));
      copy.append(top, bottom);
      button.append(copy);
      button.addEventListener("click", async () => {
        try {
          const result = await api("/api/conversations", {
            method: "POST", body: JSON.stringify({ action: "direct", username: user.username }),
          });
          $("#chat-search").value = "";
          state.userSearchQuery = "";
          state.userSearchResults = null;
          await loadConversations();
          await openConversation(result.conversation.id);
        } catch (error) { toast(error.message); }
      });
      list.append(button);
    });
  }
  function applyTranslations() {
    document.querySelectorAll(".category").forEach(button => { $(".category-label", button).textContent = t(button.dataset.filter); });
    $("#chat-search").placeholder = t("search");
    $("#empty-state h2").textContent = t("emptyTitle");
    $("#empty-state p").textContent = t("emptyBody");
    $("#empty-new-chat").textContent = t("newChat");
    $("#edit-profile-bottom").title = t("editProfile");
    $("#edit-profile-bottom").setAttribute("aria-label", t("editProfile"));
    $("#message-text").placeholder = t("writeMessage");
    $("#menu-settings-label").textContent = t("settings");
    $("#menu-contacts-label").textContent = t("contacts");
    $("#menu-new-channel-label").textContent = t("newChannel");
    $("#menu-profile-label").textContent = t("myProfile");
    $("#menu-new-group-label").textContent = t("newGroup");
    $("#menu-saved-label").textContent = t("savedMessages");
    $("#menu-night-label").textContent = t("nightMode");
    $("#menu-backdrop").querySelector(".hamburger-menu").setAttribute("aria-label", t("menuLabel"));
    updateNightModeSwitch();
  }
  function renderMessage(message) {
    const existing = document.querySelector(`[data-message-id="${message.id}"]`);
    if (existing) return;
    const item = node("article", `message${message.sender.id === state.me.id ? " mine" : ""}`);
    item.dataset.messageId = message.id;
    item.append(imageAvatar(message.sender.avatar, message.sender.display_name, "avatar message-avatar"));
    const bubble = node("div", "message-bubble");
    if (state.active?.kind !== "direct" && message.sender.id !== state.me.id) bubble.append(node("span", "message-author", message.sender.display_name));
    if (message.body) bubble.append(node("div", "message-text", message.body));
    if (message.media_url && message.media_type === "image") {
      const image = new Image(); image.className = "message-media"; image.loading = "lazy"; image.src = message.media_url; image.alt = message.media_name || "تصویر";
      image.addEventListener("click", () => openLightbox(image.src, "image")); bubble.append(image);
      const download = node("a", "message-download", "↓"); download.href = `${message.media_url}?download=1`; download.download = message.media_name || ""; download.title = "دانلود تصویر"; bubble.append(download);
    } else if (message.media_url && message.media_type === "video") {
      const video = document.createElement("video"); video.className = "message-video"; video.controls = true; video.preload = "metadata"; video.src = message.media_url; bubble.append(video);
      const download = node("a", "message-download", "↓"); download.href = `${message.media_url}?download=1`; download.download = message.media_name || ""; download.title = "دانلود ویدئو"; bubble.append(download);
    }
    bubble.append(node("time", "message-time", message.time || new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })));
    const actions = node("div", "message-actions"), save = node("button", "", "☆"); save.type = "button"; save.title = t("save");
    save.addEventListener("click", async () => { try { const result = await api(`/api/messages/${message.id}/save`, { method: "POST" }); toast(result.saved ? t("savedToast") : t("unsavedToast")); } catch (e) { toast(e.message); } });
    actions.append(save); bubble.append(actions); item.append(bubble); $("#messages-list").append(item);
  }
  function openLightbox(url, type) {
    const box = $("#lightbox-content"); box.replaceChildren();
    const media = document.createElement(type === "video" ? "video" : "img"); media.src = url;
    if (type === "video") { media.controls = true; media.autoplay = true; }
    $("#lightbox").classList.remove("hidden"); box.append(media);
  }
  async function loadConversations() {
    try {
      state.conversations = (await api("/api/conversations")).conversations;
      if (state.socket?.connected) {
        state.conversations.forEach(conversation => {
          if (Number.isInteger(conversation.id)) {
            state.socket.emit("join_conversation", { conversation_id: conversation.id });
          }
        });
      }
      renderChats();
    }
    catch (e) { toast(e.message); }
  }
  function showMessageNotification(message) {
    if (!state.me?.notifications_enabled || message.sender?.id === state.me.id) return;
    const active = state.active?.id === message.conversation_id;
    if (!document.hidden && active) return;
    const conversation = state.conversations.find(item => item.id === message.conversation_id);
    const title = conversation?.title || message.sender?.display_name || t("newMessage");
    const body = message.body || message.media_name || t("newMessage");
    if ("Notification" in window && window.Notification.permission === "granted") {
      const notification = new window.Notification(title, {
        body,
        icon: message.sender?.avatar || undefined,
        tag: `gofta-conversation-${message.conversation_id}`,
      });
      notification.onclick = () => {
        window.focus();
        openConversation(message.conversation_id);
        notification.close();
      };
    } else if (!document.hidden) {
      toast(`${title}: ${body}`);
    }
  }
  async function openConversation(id) {
    try {
      const data = await api(`/api/conversations/${id}`);
      state.active = data.conversation; state.members = data.members;
      state.lastMessageId = 0;
      $("#conversation-title").textContent = state.active.title;
      $("#conversation-subtitle").textContent = `${data.members.length} ${data.members.length === 1 ? t("member") : t("members")}`;
      const avatar = $("#conversation-avatar"), newAvatar = imageAvatar(state.active.avatar, state.active.title);
      newAvatar.id = "conversation-avatar"; avatar.replaceWith(newAvatar);
      $("#messages-list").replaceChildren(); data.messages.forEach(message => { renderMessage(message); state.lastMessageId = Math.max(state.lastMessageId, message.id); });
      $("#empty-state").classList.add("hidden"); $("#conversation-view").classList.remove("hidden");
      app.classList.add("show-conversation");
      const canPost = state.active.can_post;
      $("#message-text").disabled = !canPost; $("#attach-button").disabled = !canPost; $("#send-button").disabled = !canPost;
      $("#message-text").placeholder = canPost ? "پیامی بنویسید…" : "فقط مدیران می‌توانند در این کانال پیام بگذارند.";
      $("#members-button").classList.toggle("hidden", !["group", "channel"].includes(state.active.kind));
      $("#conversation-image-button").classList.toggle("hidden", !["group", "channel"].includes(state.active.kind) || !["owner", "admin"].includes(state.active.role));
      if (state.socket?.connected) state.socket.emit("join_conversation", { conversation_id: id });
      await api(`/api/conversations/${id}/read`, { method: "POST" });
      await loadConversations();
      requestAnimationFrame(() => { $("#messages-area").scrollTop = $("#messages-area").scrollHeight; });
    } catch (e) { toast(e.message); }
  }
  async function openSaved() {
    try {
      const result = await api("/api/saved");
      state.active = { id: "saved", kind: "saved", title: t("saved") };
      state.lastMessageId = 0;
      $("#conversation-title").textContent = t("saved"); $("#conversation-subtitle").textContent = "";
      const avatar = $("#conversation-avatar"), newAvatar = imageAvatar(null, "☆");
      newAvatar.id = "conversation-avatar"; avatar.replaceWith(newAvatar);
      $("#messages-list").replaceChildren();
      result.messages.forEach(message => { renderMessage(message); state.lastMessageId = Math.max(state.lastMessageId, message.id); });
      $("#empty-state").classList.add("hidden"); $("#conversation-view").classList.remove("hidden"); app.classList.add("show-conversation");
      $("#members-button").classList.add("hidden"); $("#conversation-image-button").classList.add("hidden");
      $("#message-text").disabled = true; $("#attach-button").disabled = true; $("#send-button").disabled = true;
    } catch (e) { toast(e.message); }
  }
  async function submitMessage(event) {
    event.preventDefault();
    if (!state.active || state.active.kind === "saved") return;
    const text = $("#message-text").value.trim(), file = state.file;
    if (!text && !file) return;
    const form = new FormData(); form.set("text", text); if (file) form.set("file", file);
    $("#send-button").disabled = true; $("#upload-status").classList.remove("hidden"); $("#upload-preview").textContent = file ? "در حال بارگذاری و ارسال…" : "در حال ارسال…";
    try {
      const result = await api(`/api/conversations/${state.active.id}/messages`, { method: "POST", body: form });
      renderMessage(result.message); $("#message-text").value = ""; clearFile();
      $("#messages-area").scrollTop = $("#messages-area").scrollHeight; await loadConversations();
    } catch (e) { toast(e.message); }
    finally { $("#send-button").disabled = !state.active.can_post; $("#upload-status").classList.add("hidden"); }
  }
  function clearFile() { state.file = null; $("#media-file").value = ""; $("#upload-status").classList.add("hidden"); $("#upload-preview").replaceChildren(); }
  function formField(label, input) { const wrapper = node("label", "", label); wrapper.append(input); return wrapper; }
  function textInput(placeholder, name, maxLength) { const input = document.createElement("input"); input.name = name; input.placeholder = placeholder; input.maxLength = maxLength; input.required = true; return input; }
  function openNewChat(initialKind = "direct") {
    const form = node("form", "modal-form");
    const kind = document.createElement("select"); kind.innerHTML = `<option value="direct">${t("direct")}</option><option value="group">${t("group")}</option><option value="channel">${t("channel")}</option>`;
    kind.value = initialKind;
    const username = textInput(t("username"), "username", 30), title = textInput(t("title"), "title", 80), members = document.createElement("input"); members.name = "members"; members.placeholder = state.me.language === "fa" ? "نام کاربری اعضا (با ویرگول جدا کنید)" : "Member usernames (comma-separated)"; members.maxLength = 400;
    const suggestions = document.createElement("datalist"); suggestions.id = "user-suggestions"; username.setAttribute("list", suggestions.id);
    username.addEventListener("input", async () => {
      if (username.value.trim().length < 2) { suggestions.replaceChildren(); return; }
      try {
        const found = await api(`/api/users?q=${encodeURIComponent(username.value.trim())}`);
        suggestions.replaceChildren(...found.users.map(user => { const option = document.createElement("option"); option.value = user.username; option.label = user.display_name; return option; }));
      } catch (e) { toast(e.message); }
    });
    const directField = formField(t("username"), username), titleField = formField(t("title"), title), memberField = formField(t("addMembers"), members);
    directField.append(suggestions);
    form.append(formField(t("type"), kind), directField, titleField, memberField);
    const updateFormFields = () => {
      const direct = kind.value === "direct";
      directField.classList.toggle("hidden", !direct); titleField.classList.toggle("hidden", direct); memberField.classList.toggle("hidden", direct);
      username.required = direct; title.required = !direct;
    };
    kind.addEventListener("change", updateFormFields);
    updateFormFields();
    const submit = node("button", "primary-button", t("create")); submit.type = "submit"; form.append(submit);
    form.addEventListener("submit", async event => {
      event.preventDefault(); const action = kind.value === "direct" ? "direct" : "create";
      const data = action === "direct" ? { action, username: username.value } : { action, kind: kind.value, title: title.value, members: members.value.split(",").map(x => x.trim()).filter(Boolean) };
      try { const result = await api("/api/conversations", { method: "POST", body: JSON.stringify(data) }); closeModal(); await loadConversations(); await openConversation(result.conversation.id); }
      catch (e) { toast(e.message); }
    });
    showModal(t("createChat"), form);
  }
  async function showMembers() {
    if (!state.active || !["group", "channel"].includes(state.active.kind)) { toast("این گفتگو فهرست اعضای مدیریتی ندارد."); return; }
    const wrap = node("div");
    if (["owner", "admin"].includes(state.active.role)) {
      const form = node("form", "form-actions"), username = textInput(state.me.language === "fa" ? "نام کاربری عضو جدید" : "New member username", "username", 30), button = node("button", "primary-button", t("addMember")); button.type = "submit"; form.append(username, button);
      form.addEventListener("submit", async event => {
        event.preventDefault(); try { await api(`/api/conversations/${state.active.id}/members`, { method: "POST", body: JSON.stringify({ username: username.value }) }); toast(t("addedToast")); showMembers(); }
        catch (e) { toast(e.message); }
      });
      wrap.append(form);
    }
    state.members.forEach(member => {
      const row = node("div", "member-row"); row.append(imageAvatar(member.avatar, member.display_name, "avatar small-avatar"));
      const info = node("span", "member-info"), roleName = member.role === "owner" ? t("owner") : member.role === "admin" ? t("admin") : t("roleMember");
      info.append(node("strong", "", member.display_name), node("small", "", `@${member.username} · ${roleName}`)); row.append(info);
      if (member.role !== "owner" && (state.active.role === "owner" || (state.active.role === "admin" && member.role === "member"))) {
        if (state.active.role === "owner") {
          const role = node("button", "secondary-button", member.role === "admin" ? t("makeMember") : t("makeAdmin"));
          role.type = "button";
          role.title = state.me.language === "fa" ? "تغییر نقش" : "Change role";
          role.addEventListener("click", async () => {
            try {
              await api(`/api/conversations/${state.active.id}/members/${member.id}`, {
                method: "PATCH", body: JSON.stringify({ role: member.role === "admin" ? "member" : "admin" }),
              });
              await refreshMembers();
            } catch (e) { toast(e.message); }
          });
          row.append(role);
        }
        const remove = node("button", "danger-button", t("remove"));
        remove.type = "button";
        remove.addEventListener("click", async () => {
          if (!window.confirm(t("removeMemberConfirm"))) return;
          try {
            await api(`/api/conversations/${state.active.id}/members/${member.id}`, { method: "DELETE" });
            await refreshMembers();
            await loadConversations();
          } catch (e) { toast(e.message); }
        });
        row.append(remove);
      }
      wrap.append(row);
    });
    showModal(t("membersTitle"), wrap);
  }
  async function refreshMembers() { const result = await api(`/api/conversations/${state.active.id}/members`); state.members = result.members; showMembers(); }
  function showConversationProfile() {
    if (!state.active) return;
    const person = state.active.kind === "direct" ? state.members.find(member => member.id !== state.me.id) : null;
    const content = node("div", "profile-editor");
    const avatar = imageAvatar(person?.avatar || state.active.avatar, person?.display_name || state.active.title);
    if (person?.avatar || state.active.avatar) avatar.addEventListener("click", () => openLightbox(person?.avatar || state.active.avatar, "image"));
    content.append(avatar, node("strong", "", person?.display_name || state.active.title));
    if (person) {
      content.append(node("span", "muted", `@${person.username}`), node("p", "muted", person.bio || ""));
    } else if (state.active.kind === "group" || state.active.kind === "channel") {
      content.append(node("span", "muted", `${state.members.length} ${t("members")}`));
    }
    showModal(person ? (state.me.language === "fa" ? "نمایهٔ کاربر" : "User profile") : state.active.title, content);
  }
  function openSettings() {
    const form = node("form", "modal-form settings-form");
    const profileFields = node("div", "profile-settings");
    const language = document.createElement("select"); language.innerHTML = `<option value="fa"${state.me.language === "fa" ? " selected" : ""}>فارسی</option><option value="en"${state.me.language === "en" ? " selected" : ""}>English</option>`;
    const theme = document.createElement("select"); theme.innerHTML = `<option value="light"${state.me.theme === "light" ? " selected" : ""}>${t("light")}</option><option value="dark"${state.me.theme === "dark" ? " selected" : ""}>${t("dark")}</option>`;
    const font = document.createElement("select"); font.innerHTML = `<option value="vazirmatn"${state.me.font_family === "vazirmatn" ? " selected" : ""}>${t("vazirmatn")}</option><option value="system"${state.me.font_family === "system" ? " selected" : ""}>${t("systemFont")}</option>`;
    const colorPicker = node("div", "palette-picker"); colorPicker.setAttribute("role", "group"); colorPicker.setAttribute("aria-label", t("colorTheme"));
    let selectedPalette = state.me.color_theme || "blue";
    const paletteButtons = [];
    Object.keys(palettes).forEach(name => {
      const button = node("button", "palette-choice"); button.type = "button"; button.dataset.palette = name;
      button.setAttribute("aria-label", t(name)); button.setAttribute("aria-pressed", String(name === selectedPalette));
      const swatch = node("span", "palette-swatch"); swatch.style.backgroundColor = palettes[name][0];
      button.append(swatch, node("span", "palette-name", t(name)));
      button.addEventListener("click", () => {
        selectedPalette = name;
        paletteButtons.forEach(item => item.setAttribute("aria-pressed", String(item.dataset.palette === name)));
        applyAppearance({ ...state.me, theme: theme.value, font_family: font.value, color_theme: name });
      });
      paletteButtons.push(button); colorPicker.append(button);
    });
    const paletteLabel = node("div", "settings-label");
    paletteLabel.append(node("span", "settings-field-icon", "◉"), node("span", "settings-field-title", t("colorTheme")), colorPicker);
    profileFields.append(
      settingsField(t("language"), "文", language),
      settingsField(t("theme"), "◐", theme),
      settingsField(t("font"), "A", font),
      paletteLabel,
    );
    const notifications = document.createElement("input");
    notifications.type = "checkbox";
    notifications.checked = state.me.notifications_enabled !== false;
    const notificationField = settingsField(t("notifications"), "♢", notifications);
    theme.addEventListener("change", () => applyAppearance({ ...state.me, theme: theme.value, font_family: font.value, color_theme: selectedPalette }));
    font.addEventListener("change", () => applyAppearance({ ...state.me, theme: theme.value, font_family: font.value, color_theme: selectedPalette }));
    const actions = node("div", "form-actions"), submit = node("button", "primary-button"); submit.type = "submit";
    submit.append(node("span", "button-icon", "✓"), document.createTextNode(t("saveProfile"))); actions.append(submit);
    const allowNotifications = node("button", "secondary-button notification-permission-button", t("allowNotifications"));
    allowNotifications.type = "button";
    allowNotifications.addEventListener("click", async () => {
      if (!("Notification" in window)) { toast(t("notificationsUnsupported")); return; }
      try {
        const permission = await window.Notification.requestPermission();
        if (permission !== "granted") { toast(t("notificationsDenied")); return; }
        notifications.checked = true;
        await api("/api/settings", { method: "POST", body: JSON.stringify({
          language: language.value, theme: theme.value, font_family: font.value,
          color_theme: selectedPalette, notifications_enabled: true,
        }) });
        state.me.notifications_enabled = true;
        toast(t("notificationsAllowed"));
      } catch (e) { toast(e.message); }
    });
    const fileManager = node("button", "secondary-button file-manager-open", t("fileManager"));
    fileManager.type = "button";
    fileManager.prepend(node("span", "button-icon", "▣"));
    fileManager.addEventListener("click", openFileManager);
    form.append(profileFields, notificationField, allowNotifications, fileManager, actions);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      try {
        await api("/api/settings", { method: "POST", body: JSON.stringify({
          language: language.value, theme: theme.value, font_family: font.value,
          color_theme: selectedPalette, notifications_enabled: notifications.checked,
        }) });
        state.me.notifications_enabled = notifications.checked;
        closeModal(); await initMe();
      } catch (e) { toast(e.message); }
    });
    showModal(t("settings"), form, "profile-sheet");
  }
  function settingsField(label, icon, input) {
    const field = node("label", "settings-field");
    field.append(node("span", "settings-field-icon", icon), node("span", "settings-field-title", label), input);
    return field;
  }
  function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    const units = ["KB", "MB", "GB"];
    let size = bytes / 1024, unit = 0;
    while (size >= 1024 && unit < units.length - 1) { size /= 1024; unit += 1; }
    return `${size.toFixed(1)} ${units[unit]}`;
  }
  async function openFileManager() {
    try {
      const data = await api("/api/files");
      const content = node("div", "file-manager");
      content.append(node("p", "muted file-manager-usage", `${t("fileUsage")}: ${formatFileSize(data.total_bytes)}`));
      const list = node("div", "file-manager-list");
      if (!data.files.length) list.append(node("p", "muted file-manager-empty", t("noFiles")));
      data.files.forEach(file => {
        const row = node("article", "file-manager-row");
        const details = node("div", "file-manager-details");
        details.append(
          node("strong", "file-manager-name", file.name || file.type),
          node("span", "muted", `${file.conversation || t("directConversation")} · ${formatFileSize(file.size)}`),
          node("time", "muted", new Date(file.created_at).toLocaleString()),
        );
        const controls = node("div", "file-manager-controls");
        const download = node("a", "secondary-button file-manager-download", t("download"));
        download.href = `${file.url}?download=1`;
        download.download = file.name || "";
        controls.append(download);
        if (file.can_delete) {
          const remove = node("button", "danger-button", t("deleteFile"));
          remove.type = "button";
          remove.addEventListener("click", async () => {
            if (!window.confirm(t("deleteFileConfirm"))) return;
            try {
              await api(`/api/files/${file.id}`, { method: "DELETE" });
              if (state.active?.id === file.conversation_id) await openConversation(file.conversation_id);
              await openFileManager();
            } catch (e) { toast(e.message); }
          });
          controls.append(remove);
        }
        row.append(details, controls);
        list.append(row);
      });
      content.append(list);
      showModal(t("fileManager"), content);
    } catch (e) { toast(e.message); }
  }
  function openProfile() {
    const form = node("form", "modal-form profile-editor"), avatar = imageAvatar(state.me.avatar, state.me.display_name);
    const file = document.createElement("input"); file.type = "file"; file.accept = "image/jpeg,image/png,image/webp,image/gif";
    const preview = node("div"); preview.append(avatar);
    file.addEventListener("change", () => { if (file.files[0]) { const img = new Image(); img.src = URL.createObjectURL(file.files[0]); avatar.replaceChildren(img); } });
    const display = textInput(t("profileName"), "display_name", 60); display.value = state.me.display_name;
    const bio = document.createElement("textarea"); bio.name = "bio"; bio.maxLength = 240; bio.value = state.me.bio || ""; bio.placeholder = t("bio");
    const phone = document.createElement("input"); phone.type = "tel"; phone.autocomplete = "tel"; phone.placeholder = "+989123456789"; phone.value = state.me.phone_input || "";
    const visibility = document.createElement("select");
    visibility.innerHTML = `<option value="private">${t("phonePrivate")}</option><option value="members">${t("phoneMembers")}</option><option value="public">${t("phonePublic")}</option>`;
    visibility.value = state.me.phone_visibility || "private";
    const phoneStatus = node("p", "muted phone-status", state.me.phone_verified ? t("phoneVerified") : t("phonePending"));
    const code = document.createElement("input"); code.inputMode = "numeric"; code.maxLength = 6; code.autocomplete = "one-time-code"; code.placeholder = t("enterCode");
    const phoneActions = node("div", "phone-actions");
    const sendCode = node("button", "secondary-button", t("sendCode")); sendCode.type = "button";
    sendCode.addEventListener("click", async () => {
      try {
        const result = await api("/api/phone/send", { method: "POST", body: JSON.stringify({ phone: phone.value }) });
        state.me.phone_input = phone.value;
        if (result.test_code) {
          code.value = result.test_code;
          phoneStatus.textContent = `${t("codeSent")}: ${result.test_code}`;
        } else {
          phoneStatus.textContent = t("phonePending");
        }
      } catch (e) { toast(e.message); }
    });
    const verify = node("button", "primary-button", t("verifyPhone")); verify.type = "button";
    verify.addEventListener("click", async () => {
      try {
        const result = await api("/api/phone/verify", { method: "POST", body: JSON.stringify({ code: code.value }) });
        state.me.phone_input = result.user.phone || phone.value;
        state.me.phone_verified = true;
        state.me.phone = result.user.phone;
        closeModal(); await initMe(); toast(t("phoneSaved")); openProfile();
      } catch (e) { toast(e.message); }
    });
    phoneActions.append(sendCode, verify);
    if (state.me.phone_input) {
      const removePhone = node("button", "danger-button", t("removePhone")); removePhone.type = "button";
      removePhone.addEventListener("click", async () => {
        try {
          await api("/api/phone", { method: "DELETE" });
          state.me.phone_input = ""; state.me.phone = null; state.me.phone_verified = false;
          closeModal(); await initMe(); toast(t("phoneRemoved")); openProfile();
        } catch (e) { toast(e.message); }
      });
      phoneActions.append(removePhone);
    }
    const actions = node("div", "form-actions"), submit = node("button", "primary-button", t("saveProfile")); submit.type = "submit"; actions.append(submit);
    if (state.me.avatar) {
      const remove = node("button", "danger-button", t("deletePicture")); remove.type = "button"; remove.addEventListener("click", async () => { const data = new FormData(); data.set("display_name", display.value); data.set("bio", bio.value); data.set("remove_avatar", "true"); try { await api("/api/profile", { method: "POST", body: data }); state.me.avatar = null; closeModal(); await initMe(); } catch (e) { toast(e.message); } }); actions.append(remove);
    }
    const logout = node("button", "secondary-button", t("signOut")); logout.type = "button"; logout.addEventListener("click", async () => { try { await api("/logout", { method: "POST" }); location.assign("/login"); } catch (e) { toast(e.message); } }); actions.append(logout);
    form.append(
      preview, formField(t("picture"), file), formField(t("profileName"), display),
      formField(t("bio"), bio), formField(t("phone"), phone), formField(t("phoneVisibility"), visibility),
      node("p", "muted phone-hint", t("phoneHint")), phoneStatus,
      formField(t("enterCode"), code), phoneActions, actions,
    );
    form.addEventListener("submit", async event => {
      event.preventDefault(); const data = new FormData(); data.set("display_name", display.value); data.set("bio", bio.value); if (file.files[0]) data.set("avatar", file.files[0]);
      data.set("phone_visibility", visibility.value);
      try {
        await api("/api/profile", { method: "POST", body: data });
        closeModal(); await initMe();
      }
      catch (e) { toast(e.message); }
    });
    showModal(t("profile"), form, "profile-sheet");
  }
  function openContacts() {
    const content = node("div", "contacts-view");
    const search = document.createElement("input"); search.type = "search"; search.autocomplete = "off";
    search.placeholder = t("searchContacts"); search.setAttribute("aria-label", t("searchContacts"));
    const results = node("div", "contact-results");
    const toolbar = node("div", "contacts-toolbar");
    const sort = node("button", "icon-button contact-sort-button", "☷"); sort.type = "button";
    sort.title = t("sortContacts"); sort.setAttribute("aria-label", t("sortContacts"));
    const add = node("button", "secondary-button contact-add-button");
    add.append(node("span", "button-icon", "+"), document.createTextNode(t("addContact")));
    add.type = "button";
    toolbar.append(sort);
    content.append(toolbar, search, results, add);
    let contacts = [];
    let adding = false;
    let ascending = true;
    let searchSequence = 0;
    const presenceText = user => {
      if (user.online) return t("online");
      if (!user.last_seen_at) return t("offline");
      const minutes = Math.max(0, Math.floor((Date.now() - new Date(user.last_seen_at).getTime()) / 60000));
      const elapsed = minutes < 1 ? (state.me.language === "fa" ? "همین حالا" : "just now")
        : minutes < 60 ? `${minutes} ${state.me.language === "fa" ? "دقیقه" : "min"}`
          : minutes < 1440 ? `${Math.floor(minutes / 60)} ${state.me.language === "fa" ? "ساعت" : "hr"}`
            : `${Math.floor(minutes / 1440)} ${state.me.language === "fa" ? "روز" : "days"}`;
      return `${t("lastSeen")} ${elapsed}`;
    };
    const openContact = async user => {
      try {
        const result = await api("/api/conversations", {
          method: "POST", body: JSON.stringify({ action: "direct", username: user.username }),
        });
        closeModal(); await loadConversations(); await openConversation(result.conversation.id);
      } catch (e) { toast(e.message); }
    };
    const renderContact = (user, canAdd = false) => {
      const item = node("div", "contact-item");
      const button = node("button", "contact-row"); button.type = "button";
      button.append(imageAvatar(user.avatar, user.display_name, "avatar small-avatar"));
      const details = node("span", "contact-details");
      details.append(
        node("strong", "", user.display_name),
        node("small", user.online ? "contact-online" : "", canAdd ? `@${user.username}` : presenceText(user)),
      );
      button.append(details);
      if (!canAdd) {
        button.addEventListener("click", () => openContact(user));
        item.append(button);
      } else {
        button.disabled = true;
        const addButton = node("button", "contact-add-result", t("addContact")); addButton.type = "button";
        addButton.addEventListener("click", async () => {
          try {
            await api("/api/contacts", { method: "POST", body: JSON.stringify({ username: user.username }) });
            toast(t("contactAdded")); contacts = (await api("/api/contacts")).contacts;
            adding = false; search.value = ""; search.placeholder = t("searchContacts"); renderContacts();
          } catch (e) { toast(e.message); }
        });
        item.append(button, addButton);
      }
      results.append(item);
    };
    const renderContacts = () => {
      results.replaceChildren();
      const query = search.value.trim().toLocaleLowerCase();
      if (adding) {
        if (query.length < 2) {
          results.append(node("p", "muted contacts-hint", t("contactsHint")));
          return;
        }
        const sequence = ++searchSequence;
        api(`/api/users?q=${encodeURIComponent(query)}`).then(response => {
          if (!adding || sequence !== searchSequence) return;
          const known = new Set(contacts.map(user => user.id));
          const users = response.users.filter(user => !known.has(user.id));
          if (!users.length) results.append(node("p", "muted contacts-hint", t("noContacts")));
          users.forEach(user => renderContact(user, true));
        }).catch(error => toast(error.message));
        return;
      }
      const visible = contacts.filter(user => `${user.display_name} ${user.username}`.toLocaleLowerCase().includes(query));
      visible.sort((a, b) => {
        if (a.online !== b.online) return a.online ? -1 : 1;
        const order = a.display_name.localeCompare(b.display_name);
        return ascending ? order : -order;
      });
      if (!visible.length) {
        results.append(node("p", "muted contacts-hint", contacts.length ? t("noContacts") : t("contactsNone")));
        return;
      }
      visible.forEach(user => renderContact(user));
    };
    search.addEventListener("input", async () => {
      renderContacts();
    });
    add.addEventListener("click", () => {
      adding = !adding; search.value = "";
      search.placeholder = adding ? t("searchContacts") : t("searchContacts");
      search.focus(); renderContacts();
    });
    sort.addEventListener("click", () => { ascending = !ascending; renderContacts(); });
    showModal(t("contacts"), content, "contacts-sheet");
    api("/api/contacts").then(response => { contacts = response.contacts; renderContacts(); }).catch(error => toast(error.message));
  }
  function openHamburgerMenu() {
    $("#menu-name").textContent = state.me.display_name;
    $("#menu-phone").textContent = state.me.phone || "";
    $("#menu-username").textContent = `@${state.me.username}`;
    const old = $("#menu-avatar"), avatar = imageAvatar(state.me.avatar, state.me.display_name);
    avatar.id = "menu-avatar";
    old.replaceWith(avatar);
    $("#menu-backdrop").classList.remove("hidden");
  }
  function closeHamburgerMenu() { $("#menu-backdrop").classList.add("hidden"); }
  async function changeConversationImage() {
    const input = document.createElement("input"); input.type = "file"; input.accept = "image/jpeg,image/png,image/webp,image/gif";
    input.addEventListener("change", async () => { if (!input.files[0]) return; const form = new FormData(); form.set("avatar", input.files[0]); try { await api(`/api/conversations/${state.active.id}/avatar`, { method: "POST", body: form }); await openConversation(state.active.id); } catch (e) { toast(e.message); } });
    input.click();
  }
  async function initMe() {
    const me = await api("/api/me"); state.me = me; applyAppearance(me);
    document.documentElement.lang = me.language; document.documentElement.dir = me.language === "fa" ? "rtl" : "ltr";
    applyTranslations();
    $("#menu-settings-label").textContent = t("settings");
    $("#menu-contacts-label").textContent = t("contacts");
    $("#menu-name").textContent = me.display_name;
    $("#menu-phone").textContent = me.phone || "";
    $("#menu-username").textContent = `@${me.username}`;
    updateNightModeSwitch();
    const oldAvatar = $("#menu-avatar"), newAvatar = imageAvatar(me.avatar, me.display_name);
    newAvatar.id = "menu-avatar"; oldAvatar.replaceWith(newAvatar);
    if (!state.socket && window.io) {
      state.socket = window.io({ transports: ["websocket", "polling"] });
      state.socket.on("connect", () => { loadConversations(); });
      state.socket.on("new_message", message => {
        const incoming = { ...message, mine: message.sender?.id === state.me.id };
        if (state.active?.id === message.conversation_id) { renderMessage(incoming); state.lastMessageId = Math.max(state.lastMessageId, message.id); $("#messages-area").scrollTop = $("#messages-area").scrollHeight; }
        showMessageNotification(message);
        loadConversations();
      });
      state.socket.on("conversation_added", () => loadConversations());
      state.socket.on("conversation_removed", data => {
        state.socket.emit("leave_conversation", { conversation_id: data.conversation_id });
        state.conversations = state.conversations.filter(item => item.id !== data.conversation_id);
        if (state.active?.id === data.conversation_id) {
          state.active = null;
          state.members = [];
          $("#conversation-view").classList.add("hidden");
          $("#empty-state").classList.remove("hidden");
          app.classList.remove("show-conversation");
        }
        renderChats();
        toast(t("removedFromConversation"));
      });
      state.socket.on("media_removed", data => {
        if (state.active?.id === data.conversation_id) openConversation(data.conversation_id);
        loadConversations();
      });
      state.socket.on("message_error", data => toast(data.error));
    }
    await loadConversations();
  }
  async function pollActiveConversation() {
    if (!Number.isInteger(state.active?.id)) return;
    try {
      const result = await api(`/api/conversations/${state.active.id}/messages?after=${state.lastMessageId}`);
      state.pollError = null;
      if (result.messages.length) {
        result.messages.forEach(message => { renderMessage(message); state.lastMessageId = Math.max(state.lastMessageId, message.id); });
        $("#messages-area").scrollTop = $("#messages-area").scrollHeight;
        await loadConversations();
      }
    } catch (e) {
      if (state.pollError !== e.message) toast(e.message);
      state.pollError = e.message;
    }
  }
  $("#edit-profile-bottom").addEventListener("click", openProfile);
  $("#empty-new-chat").addEventListener("click", () => openNewChat());
  $("#message-form").addEventListener("submit", submitMessage);
  $("#attach-button").addEventListener("click", () => $("#media-file").click());
  $("#media-file").addEventListener("change", event => {
    const file = event.target.files[0]; if (!file) return; state.file = file;
    const preview = $("#upload-preview"); preview.replaceChildren();
    const media = document.createElement(file.type.startsWith("video/") ? "video" : "img"); media.src = URL.createObjectURL(file); media.alt = file.name;
    if (media.tagName === "VIDEO") media.muted = true; preview.append(media, document.createTextNode(`${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB`));
    $("#upload-status").classList.remove("hidden");
  });
  $("#cancel-upload").addEventListener("click", clearFile);
  $("#chat-search").addEventListener("input", renderChats);
  document.querySelectorAll(".category").forEach(button => button.addEventListener("click", () => {
    document.querySelector(".category.active")?.classList.remove("active"); button.classList.add("active"); state.filter = button.dataset.filter; renderChats();
  }));
  $("#members-button").addEventListener("click", showMembers);
  $("#conversation-image-button").addEventListener("click", changeConversationImage);
  $("#conversation-info").addEventListener("click", showConversationProfile);
  $("#back-button").addEventListener("click", () => app.classList.remove("show-conversation"));
  $("#modal-close").addEventListener("click", closeModal);
  $("#modal-backdrop").addEventListener("click", event => { if (event.target.id === "modal-backdrop") closeModal(); });
  $("#lightbox-close").addEventListener("click", () => { $("#lightbox").classList.add("hidden"); $("#lightbox-content").replaceChildren(); });
  $("#lightbox").addEventListener("click", event => { if (event.target.id === "lightbox") $("#lightbox-close").click(); });
  $("#menu-button").addEventListener("click", () => { if (state.me) openHamburgerMenu(); });
  $("#menu-my-profile").addEventListener("click", () => { closeHamburgerMenu(); openProfile(); });
  $("#menu-new-group").addEventListener("click", () => { closeHamburgerMenu(); openNewChat("group"); });
  $("#menu-contacts").addEventListener("click", () => { closeHamburgerMenu(); openContacts(); });
  $("#menu-saved").addEventListener("click", () => { closeHamburgerMenu(); openSaved(); });
  $("#menu-settings").addEventListener("click", () => { closeHamburgerMenu(); openSettings(); });
  $("#menu-new-channel").addEventListener("click", () => { closeHamburgerMenu(); openNewChat("channel"); });
  $("#menu-night-mode").addEventListener("click", async () => {
    const theme = state.me.theme === "dark" ? "light" : "dark";
    try {
      await api("/api/settings", { method: "POST", body: JSON.stringify({
        language: state.me.language, theme, font_family: state.me.font_family, color_theme: state.me.color_theme,
      }) });
      state.me.theme = theme;
      applyAppearance(state.me);
      updateNightModeSwitch();
    } catch (e) { toast(e.message); }
  });
  $("#menu-close").addEventListener("click", closeHamburgerMenu);
  $("#menu-backdrop").addEventListener("click", event => { if (event.target.id === "menu-backdrop") closeHamburgerMenu(); });
  $("#message-text").addEventListener("input", event => { event.target.style.height = "auto"; event.target.style.height = `${Math.min(event.target.scrollHeight, 135)}px`; });
  window.setInterval(pollActiveConversation, 2500);
  initMe().catch(error => toast(error.message));
})();
