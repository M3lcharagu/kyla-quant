// Non-production control-channel skeleton. Review before any real deployment.
const path = require("node:path");
const {
  default: makeWASocket,
  Browsers,
  DisconnectReason,
  useMultiFileAuthState,
} = require("@whiskeysockets/baileys");

const AUTH_DIR = path.join(__dirname, "auth_info_baileys");

async function start() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const sock = makeWASocket({
    auth: state,
    browser: Browsers.ubuntu("Kyla WhatsApp Skeleton"),
    printQRInTerminal: true,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", ({ connection, lastDisconnect }) => {
    if (connection === "open") {
      console.log("Connected: non-production WhatsApp skeleton is ready.");
    }

    if (connection === "close") {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      if (shouldReconnect) {
        setTimeout(() => start().catch(console.error), 3000);
      } else {
        console.error("Logged out; remove the local session only after review.");
      }
    }
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;

    const message = messages[0];
    if (!message?.message || message.key.fromMe) return;

    const jid = message.key.remoteJid;
    if (!jid || jid === "status@broadcast") return;

    const text = (
      message.message.conversation ||
      message.message.extendedTextMessage?.text ||
      ""
    ).trim();
    if (!text) return;

    const command = text.toLowerCase().split(/\s+/)[0];
    const replies = {
      "/status": "Kyla control channel skeleton: online, non-production, no live trading.",
      "/trade": "Paper-trading placeholder only. No live order execution is implemented.",
      "/content": "Content lane placeholder: run content/daily_content_plan.py for a local plan.",
      "/help": "Commands: /status, /trade, /content, /help. Other text is echoed.",
    };

    await sock.sendMessage(jid, {
      text: replies[command] || `Echo: ${text}`,
    });
  });
}

start().catch((error) => {
  console.error("WhatsApp skeleton stopped:", error);
  process.exitCode = 1;
});
