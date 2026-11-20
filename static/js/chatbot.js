document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("chatbot-toggle");
    const closeButton = document.getElementById("chatbot-close");
    const chatbotWindow = document.getElementById("chatbot-window");
    const ctaChatbot = document.getElementById("cta-chatbot");

    const input = document.getElementById("chatbot-input");
    const sendButton = document.getElementById("chatbot-send");
    const messages = document.getElementById("chatbot-messages");

    // Open chatbot window
    function openChatbot() {
        if (chatbotWindow) {
            chatbotWindow.style.display = "flex";
            if (input) {
                setTimeout(function () { input.focus(); }, 120);
            }
        }
    }

    // Auto-open if URL has #chatbot-open hash
    if (window.location.hash === "#chatbot-open") {
        openChatbot();
    }

    if (toggleButton) toggleButton.addEventListener("click", openChatbot);
    if (ctaChatbot) ctaChatbot.addEventListener("click", openChatbot);

    // Close chatbot window
    if (closeButton) {
        closeButton.addEventListener("click", function () {
            if (chatbotWindow) chatbotWindow.style.display = "none";
        });
    }

    // Retrieve CSRF token from input, cookie, or meta
    function getCSRFToken() {
        const tokenInput = document.getElementById("chatbot-csrf-token") ||
                           document.querySelector("input[name='csrfmiddlewaretoken']");
        if (tokenInput && tokenInput.value) {
            return tokenInput.value;
        }

        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith("csrftoken=")) {
                return cookie.substring("csrftoken=".length);
            }
        }
        return "";
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        if (messages) {
            messages.scrollTop = messages.scrollHeight;
        }
    }

    // Add normal message bubble
    function addMessage(text, type) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add(type === "user" ? "user-message" : "bot-message");
        messageDiv.textContent = text;
        messages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Add rich department recommendation card with Book Appointment button directly in chat
    function addRecommendationCard(data) {
        const cardDiv = document.createElement("div");
        cardDiv.classList.add("bot-message", "rec-chat-card");

        const deptName = data.department || "General Medicine";
        const confidence = data.confidence_percentage ? `${data.confidence_percentage}% Match` : "Recommended";
        const description = (data.department_details && data.department_details.description) ||
                            (data.database && data.database.description) ||
                            "Specialized hospital department recommended for your described symptoms.";
        const bookingUrl = (data.database && data.database.booking_url) || `/booking/?dept=${encodeURIComponent(deptName)}`;

        // Emergency warning banner
        let emergencyHtml = "";
        if (data.is_emergency && data.emergency_message) {
            emergencyHtml = `
                <div class="rec-emergency-banner" style="background:#fee2e2; border:1px solid #fca5a5; border-radius:8px; padding:9px 11px; color:#991b1b; font-size:12px; font-weight:600; line-height:1.4; margin-bottom:10px;">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <strong>Emergency Alert:</strong> ${data.emergency_message}
                </div>
            `;
        }

        // Available Doctors list
        let doctorText = "";
        if (data.database && data.database.doctors && data.database.doctors.length > 0) {
            const docList = data.database.doctors.map(d => d.doc_name).join(", ");
            doctorText = `<div style="font-size:11px; color:#1e40af; margin-bottom:8px; line-height:1.35;"><strong>Available Specialists:</strong> ${docList}</div>`;
        }

        cardDiv.innerHTML = `
            <div class="rec-chat-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
                <span class="rec-pill" style="background:#e0edff; color:#1854d9; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; padding:3px 8px; border-radius:10px;"><i class="fa-solid fa-brain"></i> AI Department Recommendation</span>
                <span class="rec-conf" style="background:#ecfdf5; color:#059669; font-size:11px; font-weight:700; padding:3px 8px; border-radius:10px; border:1px solid #a7f3d0;"><i class="fa-solid fa-circle-check"></i> ${confidence}</span>
            </div>
            <div class="rec-dept-name" style="font-size:16px; font-weight:700; color:#0f172a; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                <i class="fa-solid fa-hospital text-primary"></i> ${deptName}
            </div>
            ${emergencyHtml}
            <div class="rec-dept-desc" style="font-size:12px; color:#475569; line-height:1.45; margin-bottom:10px;">${description}</div>
            ${doctorText}
            <a href="${bookingUrl}" class="rec-book-btn" style="display:flex; align-items:center; justify-content:center; gap:6px; background:#1854d9; color:#ffffff !important; font-size:13px; font-weight:600; padding:10px 14px; border-radius:8px; text-decoration:none; text-align:center; margin-bottom:8px; box-shadow:0 2px 6px rgba(24,84,217,0.25);">
                <i class="fa-solid fa-calendar-check"></i> Book Appointment with ${deptName}
            </a>
            <div class="rec-disclaimer" style="font-size:10px; color:#94a3b8; line-height:1.35; border-top:1px solid #f1f5f9; padding-top:6px;">
                ⚠️ Medical Disclaimer: Recommendation for hospital guidance only. Not a medical diagnosis or prescription.
            </div>
        `;

        messages.appendChild(cardDiv);
        scrollToBottom();
    }

    // Process user symptoms or message
    async function processUserMessage(rawText) {
        const text = (rawText || "").trim();

        if (!text) {
            if (input) input.focus();
            return;
        }

        // Show user message in chat
        addMessage(text, "user");
        if (input) input.value = "";

        // Add animated loading indicator
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("bot-message", "loading-message");
        loadingDiv.id = "chatbot-loading";
        loadingDiv.style.cssText = "display:flex; align-items:center; gap:8px; padding:10px 14px !important; background:#ffffff !important; border:1px solid #e2e8f0; color:#64748b; font-size:12px;";
        loadingDiv.innerHTML = `
            <div class="typing-indicator" style="display:flex; align-items:center; gap:4px;">
                <span style="display:inline-block; width:6px; height:6px; background:#1854d9; border-radius:50%;"></span>
                <span style="display:inline-block; width:6px; height:6px; background:#1854d9; border-radius:50%;"></span>
                <span style="display:inline-block; width:6px; height:6px; background:#1854d9; border-radius:50%;"></span>
            </div>
            <span>Analyzing symptoms with AI model...</span>
        `;
        messages.appendChild(loadingDiv);
        scrollToBottom();

        if (sendButton) sendButton.disabled = true;

        try {
            // First call recommendation API
            const response = await fetch("/chatbot/api/recommend/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ symptoms: text })
            });

            const data = await response.json();

            if (data.success) {
                addRecommendationCard(data);
            } else {
                // If recommendation says input empty or too short, fallback to conversational chat
                const chatResp = await fetch("/chatbot/api/chat/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken()
                    },
                    body: JSON.stringify({ message: text })
                });
                const chatData = await chatResp.json();
                if (chatData.success && chatData.response) {
                    addMessage(chatData.response, "bot");
                } else {
                    addMessage(data.error || "Please describe your symptoms in more detail so I can recommend the right department.", "bot");
                }
            }

        } catch (error) {
            console.error("Chatbot Error:", error);
            addMessage("Unable to connect to the recommendation engine. Please try again.", "bot");
        } finally {
            // Always safely remove loading indicator
            if (loadingDiv && loadingDiv.parentNode) {
                loadingDiv.parentNode.removeChild(loadingDiv);
            }
            if (sendButton) {
                sendButton.disabled = false;
            }
            if (input) {
                input.focus();
            }
            scrollToBottom();
        }
    }

    // Send button click
    if (sendButton) {
        sendButton.addEventListener("click", function () {
            processUserMessage(input.value);
        });
    }

    // Enter key press
    if (input) {
        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                processUserMessage(input.value);
            }
        });
    }

    // Quick symptom chips click handler
    document.addEventListener("click", function (event) {
        const chip = event.target.closest(".chat-symptom-chip");
        if (chip) {
            const query = chip.getAttribute("data-symptom") || chip.textContent.trim();
            if (query) {
                processUserMessage(query);
            }
        }
    });
});
