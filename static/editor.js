(function () {
    const btn = document.getElementById("insertMediaBtn");
    const fileInput = document.getElementById("mediaFileInput");
    const status = document.getElementById("uploadStatus");
    const textarea = document.getElementById("content");

    if (!btn || !fileInput || !textarea) return;

    btn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", async function () {
        const file = this.files[0];
        if (!file) return;

        setStatus("loading", "Uploading…");
        btn.disabled = true;

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("/admin/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                setStatus("error", data.error || "Upload failed.");
                return;
            }

            const snippet = buildSnippet(data, file.name);
            insertAtCursor(textarea, snippet);

            setStatus("success", "✓ Inserted!");
            setTimeout(() => setStatus("", ""), 2500);
        } catch (err) {
            setStatus("error", "Network error — upload failed.");
        } finally {
            btn.disabled = false;
            fileInput.value = "";
        }
    });

    function buildSnippet(data, originalName) {
        if (data.type === "video") {
            return `<video controls src="${data.url}" style="max-width:100%;border-radius:6px;"></video>`;
        }
        const alt = originalName.replace(/\.[^.]+$/, "");
        return `![${alt}](${data.url})`;
    }
    
    function insertAtCursor(el, text) {
        const start = el.selectionStart;
        const end = el.selectionEnd;
        const before = el.value.substring(0, start);
        const after = el.value.substring(end);

        const prefix = before.length > 0 && !before.endsWith("\n") ? "\n" : "";
        const suffix = after.length > 0 && !after.startsWith("\n") ? "\n" : "";

        el.value = before + prefix + text + suffix + after;

        const newPos = start + prefix.length + text.length;
        el.selectionStart = newPos;
        el.selectionEnd = newPos;
        el.focus();
    }

    function setStatus(type, message) {
        if (!status) return;
        status.textContent = message;
        status.className = "upload-status" + (type ? ` upload-status--${type}` : "");
    }
})()