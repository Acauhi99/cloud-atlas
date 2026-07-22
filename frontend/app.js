const API_BASE_URL = window.CLOUD_ATLAS_API_URL || "http://localhost:8000/v1";

async function apiRequest(path, { method = "GET", userId, body } = {}) {
  const headers = { "X-User-ID": userId };

  if (body !== undefined) headers["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error("Unable to reach the API");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const message = typeof error.detail === "string" ? error.detail : error.title;
    throw new Error(message || `HTTP ${response.status}`);
  }

  if (response.status === 204) return undefined;
  return response.json();
}

function app() {
  const NAME_RE = /^[a-z0-9_-]{3,64}$/;
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  function validateName(value) {
    if (!value) return "Name is required";
    if (value.length < 3) return "Minimum 3 characters";
    if (value.length > 64) return "Maximum 64 characters";
    if (!NAME_RE.test(value)) return "Only lowercase letters, digits, underscore, hyphen";
    return null;
  }

  return {
    userId: "",
    userPreset: "",
    search: "",
    tags: [],
    expanded: {},
    loading: false,

    modal: {
      open: false,
      type: "",
      mode: "",
      title: "",
      tagId: null,
      valueId: null,
      form: { name: "", description: "", values: [] },
      errors: { name: null },
    },

    confirmDel: {
      open: false,
      type: "",
      message: "",
      data: null,
      loading: false,
    },

    toasts: [],

    get filteredTags() {
      if (!this.search) return this.tags;
      const q = this.search.toLowerCase();
      return this.tags.filter(t => t.name.includes(q));
    },

    init() {
      this.userId = localStorage.getItem("ca_user_id") || "";
    },

    isValidUUID(v) { return UUID_RE.test(v || ""); },

    generateUserId() {
      this.userId = crypto.randomUUID();
      this.userPreset = "";
      localStorage.setItem("ca_user_id", this.userId);
      this.loadTags();
    },

    switchUser() {
      if (this.userPreset) this.userId = this.userPreset;
      else this.userId = "";
      this.loadTags();
    },

    $watch_userId() {
      localStorage.setItem("ca_user_id", this.userId);
    },

    async loadTags() {
      this.$watch_userId();
      if (!this.userId || !this.isValidUUID(this.userId)) {
        this.tags = [];
        return;
      }
      this.loading = true;
      try {
        const data = await apiRequest("/tags?page_size=100", { userId: this.userId });
        this.tags = data.items;
      } catch (e) {
        this.toast(e.message, "error");
      } finally {
        this.loading = false;
      }
    },

    toggleExpand(id) { this.expanded[id] = !this.expanded[id]; },

    toast(message, type = "info") {
      const id = Date.now() + Math.random();
      this.toasts.push({ id, message, type, visible: true });
      setTimeout(() => {
        const t = this.toasts.find(x => x.id === id);
        if (t) t.visible = false;
        setTimeout(() => { this.toasts = this.toasts.filter(x => x.id !== id); }, 300);
      }, 3000);
    },

    closeModal() { this.modal.open = false; },

    resetModal() {
      this.modal = {
        open: true, type: "", mode: "", title: "",
        tagId: null, valueId: null,
        form: { name: "", description: "", values: [] },
        errors: { name: null },
      };
    },

    openNewTagModal() {
      if (!this.userId || !this.isValidUUID(this.userId)) {
        this.toast("Set a valid User ID first", "error");
        return;
      }
      this.resetModal();
      this.modal.type = "tag";
      this.modal.mode = "create";
      this.modal.title = "New Tag";
    },

    openEditTagModal(tag) {
      this.resetModal();
      this.modal.type = "tag";
      this.modal.mode = "edit";
      this.modal.title = "Edit Tag";
      this.modal.tagId = tag.id;
      this.modal.form.name = tag.name;
      this.modal.form.description = tag.description || "";
    },

    openNewValueModal(tag) {
      this.resetModal();
      this.modal.type = "value";
      this.modal.mode = "create";
      this.modal.title = "New Value";
      this.modal.tagId = tag.id;
    },

    openEditValueModal(tag, value) {
      this.resetModal();
      this.modal.type = "value";
      this.modal.mode = "edit";
      this.modal.title = "Edit Value";
      this.modal.tagId = tag.id;
      this.modal.valueId = value.id;
      this.modal.form.name = value.name;
      this.modal.form.description = value.description || "";
    },

    validateName(field) {
      this.modal.errors[field] = validateName(this.modal.form[field]);
    },

    validateValueName(idx) {
      const val = this.modal.form.values[idx];
      val.error = validateName(val.name);
    },

    addValueRow() {
      this.modal.form.values.push({ name: "", description: "", error: null });
    },

    removeValueRow(idx) {
      this.modal.form.values.splice(idx, 1);
    },

    isTagFormValid() {
      if (validateName(this.modal.form.name)) return false;
      if (this.modal.mode === "create") {
        const filledValues = this.modal.form.values.filter(v => v.name.trim());
        return filledValues.every(v => !validateName(v.name));
      }
      return true;
    },

    isValueFormValid() {
      return !validateName(this.modal.form.name);
    },

    async submitTagForm() {
      this.validateName("name");
      if (this.modal.errors.name) return;

      try {
        if (this.modal.mode === "create") {
          const values = this.modal.form.values
            .filter(v => v.name.trim())
            .map(v => ({ name: v.name.trim(), description: v.description.trim() || null }));
          const invalidValues = values.filter(v => validateName(v.name));
          if (invalidValues.length > 0) {
            this.toast("Invalid value names", "error");
            return;
          }
          await apiRequest("/tags", {
            method: "POST",
            userId: this.userId,
            body: {
              name: this.modal.form.name.trim(),
              description: this.modal.form.description.trim() || null,
              values,
            },
          });
          this.toast("Tag created", "success");
        } else {
          await apiRequest(`/tags/${this.modal.tagId}`, {
            method: "PATCH",
            userId: this.userId,
            body: {
              name: this.modal.form.name.trim(),
              description: this.modal.form.description.trim() || null,
            },
          });
          this.toast("Tag updated", "success");
        }
        this.closeModal();
        this.loadTags();
      } catch (e) {
        this.toast(e.message, "error");
      }
    },

    async submitValueForm() {
      this.validateName("name");
      if (this.modal.errors.name) return;

      try {
        if (this.modal.mode === "create") {
          await apiRequest(`/tags/${this.modal.tagId}/values`, {
            method: "POST",
            userId: this.userId,
            body: {
              name: this.modal.form.name.trim(),
              description: this.modal.form.description.trim() || null,
            },
          });
          this.toast("Value created", "success");
        } else {
          await apiRequest(`/tags/${this.modal.tagId}/values/${this.modal.valueId}`, {
            method: "PATCH",
            userId: this.userId,
            body: {
              name: this.modal.form.name.trim(),
              description: this.modal.form.description.trim() || null,
            },
          });
          this.toast("Value updated", "success");
        }
        this.closeModal();
        this.loadTags();
      } catch (e) {
        this.toast(e.message, "error");
      }
    },

    requestDelete(type, data) {
      if (type === "tag") {
        this.confirmDel = {
          open: true, type: "tag",
          message: `Delete tag "${data.name}" and all its values? This cannot be undone.`,
          data: { id: data.id }, loading: false,
        };
      } else {
        this.confirmDel = {
          open: true, type: "value",
          message: `Delete value "${data.value.name}" from tag "${data.tag.name}"?`,
          data: { tagId: data.tag.id, valueId: data.value.id }, loading: false,
        };
      }
    },

    cancelDelete() { this.confirmDel.open = false; },

    async confirmDelete() {
      this.confirmDel.loading = true;
      try {
        if (this.confirmDel.type === "tag") {
          await apiRequest(`/tags/${this.confirmDel.data.id}`, {
            method: "DELETE",
            userId: this.userId,
          });
          delete this.expanded[this.confirmDel.data.id];
          this.toast("Tag deleted", "success");
        } else {
          await apiRequest(
            `/tags/${this.confirmDel.data.tagId}/values/${this.confirmDel.data.valueId}`,
            { method: "DELETE", userId: this.userId },
          );
          this.toast("Value deleted", "success");
        }
        this.cancelDelete();
        this.loadTags();
      } catch (e) {
        this.toast(e.message, "error");
      } finally {
        this.confirmDel.loading = false;
      }
    },
  };
}
