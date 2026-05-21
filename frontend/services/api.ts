export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Upload failed");
  }

  return response.json();
};

export const uploadFileWithProgress = (file: File, onProgress: (pct: number) => void): Promise<any> => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        onProgress(percentComplete);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText);
          resolve(res);
        } catch (e) {
          resolve({ filename: file.name });
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || "Upload failed"));
        } catch (e) {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Network error during upload"));
    });

    xhr.addEventListener("abort", () => {
      reject(new Error("Upload aborted by user"));
    });

    xhr.open("POST", `${API_BASE_URL}/upload`);
    xhr.send(formData);
  });
};

export const getFileStatus = async (filename: string) => {
  const response = await fetch(`${API_BASE_URL}/files/${encodeURIComponent(filename)}/status`);
  if (!response.ok) {
    throw new Error("Failed to get status");
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
  if (!response.ok) {
    throw new Error("Failed to list files");
  }
  return response.json();
};

export const deleteFile = async (filename: string) => {
  const response = await fetch(`${API_BASE_URL}/delete-file`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  if (!response.ok) {
    throw new Error("Delete request failed");
  }
  return response.json();
};

export const clearAllData = async () => {
  const response = await fetch(`${API_BASE_URL}/clear-all`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Clear request failed");
  }
  return response.json();
};
