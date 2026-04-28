const API_BASE_URL = "http://localhost:8000/api";

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Upload failed");
  }

  return response.json();
};

export const sendMessage = async (question: string, selectedDocs?: string[]) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, selected_docs: selectedDocs }),
  });

  if (!response.ok) {
    throw new Error("Chat request failed");
  }

  return response.json();
};

export const searchDocuments = async (query: string, selectedDocs?: string[]) => {
  const response = await fetch(`${API_BASE_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, selected_docs: selectedDocs }),
  });

  if (!response.ok) {
    throw new Error("Search request failed");
  }

  return response.json();
};

export const listFiles = async () => {
  const response = await fetch(`${API_BASE_URL}/files`);
  return response.json();
};

export const deleteFile = async (filename: string) => {
  const response = await fetch(`${API_BASE_URL}/delete-file`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  return response.json();
};

export const clearAllData = async () => {
  const response = await fetch(`${API_BASE_URL}/clear-all`, {
    method: "DELETE",
  });
  return response.json();
};
