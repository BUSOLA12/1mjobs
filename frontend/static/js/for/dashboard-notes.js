/*
 * Dashboard Notes: personal reminders a user can add, edit and delete.
 * Backed by /api/users/notes/ (list/create) and /api/users/notes/<id>/.
 */
(function () {
    "use strict";
    const API = "/api/users/notes/";
    const LABEL = { low: "Low Priority", medium: "Medium Priority", high: "High Priority" };
    let editingId = null;

    function esc(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, c => (
            { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
        ));
    }

    function noteHtml(n) {
        const pr = LABEL[n.priority] ? n.priority : "medium";
        return (
            '<div class="dashboard-note" data-note-id="' + n.id + '">' +
                "<p>" + esc(n.text) + "</p>" +
                '<div class="note-footer">' +
                    '<span class="note-priority ' + pr + '">' + LABEL[pr] + "</span>" +
                    '<div class="note-buttons">' +
                        '<a href="#" class="note-edit" title="Edit" data-tippy-placement="top"><i class="icon-feather-edit"></i></a>' +
                        '<a href="#" class="note-delete" title="Remove" data-tippy-placement="top"><i class="icon-feather-trash-2"></i></a>' +
                    "</div>" +
                "</div>" +
            "</div>"
        );
    }

    async function loadNotes() {
        const list = document.getElementById("notes-list");
        if (!list) return;
        try {
            const res = await fetchProtected(API);
            if (!res || !res.ok) return;
            const notes = await res.json();
            if (!Array.isArray(notes) || notes.length === 0) {
                list.innerHTML = '<div class="notes-empty">You have no notes yet. Add one to remember something.</div>';
                return;
            }
            list.innerHTML = notes.map(noteHtml).join("");
        } catch (e) {
            console.error("Failed to load notes:", e);
        }
    }

    function setPriority(val) {
        const sel = document.getElementById("note-priority");
        if (!sel) return;
        sel.value = val;
        if (window.jQuery && jQuery(sel).selectpicker) jQuery(sel).selectpicker("val", val);
    }
    function getPriority() {
        const sel = document.getElementById("note-priority");
        return (sel && sel.value) || "medium";
    }

    function resetForm() {
        editingId = null;
        const t = document.getElementById("note-text");
        if (t) t.value = "";
        setPriority("medium");
    }

    function openPopup() {
        if (window.jQuery && jQuery.magnificPopup) {
            jQuery.magnificPopup.open({ items: { src: "#small-dialog" }, type: "inline" });
        }
    }
    function closePopup() {
        if (window.jQuery && jQuery.magnificPopup) jQuery.magnificPopup.close();
    }

    async function submitNote(e) {
        if (e) e.preventDefault();
        const t = document.getElementById("note-text");
        const text = t ? t.value.trim() : "";
        const priority = getPriority();
        if (!text) {
            if (window.Snackbar) Snackbar.show({
                text: "Write something for your note.", pos: "bottom-center",
                showAction: false, duration: 2500, backgroundColor: "#e74c3c", textColor: "#fff"
            });
            return;
        }
        const url = editingId ? API + editingId + "/" : API;
        const method = editingId ? "PUT" : "POST";
        try {
            const res = await fetchProtected(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, priority: priority }),
            });
            if (!res || !res.ok) return;
            closePopup();
            resetForm();
            loadNotes();
        } catch (err) {
            console.error("Failed to save note:", err);
        }
    }

    async function deleteNote(id) {
        try {
            const res = await fetchProtected(API + id + "/", { method: "DELETE" });
            if (res && (res.ok || res.status === 204)) loadNotes();
        } catch (e) {
            console.error("Failed to delete note:", e);
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        loadNotes();

        // Opening the popup via the "Add Note" button starts a fresh note.
        document.querySelectorAll('.add-note-button a[href="#small-dialog"]').forEach(function (el) {
            el.addEventListener("click", resetForm);
        });

        // The submit button uses form="add-note", so a click submits the form.
        const form = document.getElementById("add-note");
        if (form) form.addEventListener("submit", submitNote);

        // Edit / delete via delegation on the list.
        const list = document.getElementById("notes-list");
        if (list) {
            list.addEventListener("click", function (e) {
                const noteEl = e.target.closest(".dashboard-note");
                if (!noteEl) return;
                const id = noteEl.getAttribute("data-note-id");
                if (e.target.closest(".note-edit")) {
                    e.preventDefault();
                    editingId = id;
                    const text = (noteEl.querySelector("p") || {}).textContent || "";
                    const prSpan = noteEl.querySelector(".note-priority");
                    const pr = prSpan
                        ? (prSpan.classList.contains("high") ? "high"
                            : prSpan.classList.contains("low") ? "low" : "medium")
                        : "medium";
                    const t = document.getElementById("note-text");
                    if (t) t.value = text;
                    setPriority(pr);
                    openPopup();
                } else if (e.target.closest(".note-delete")) {
                    e.preventDefault();
                    deleteNote(id);
                }
            });
        }
    });
})();
