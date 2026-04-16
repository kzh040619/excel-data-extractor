import { useEffect, useState } from 'react';

export interface FileInfo {
  id: string;
  fileName: string;
  storedPath: string;
  sheets: string[];
  sheetName: string;
  columns: string[];
  lastModified: string;
  lastUsedAt: string;
}

export interface FilterItem {
  field: string;
  operator: string;
  value: string;
}

export interface ExportPreviewResult {
  count: number;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface QuickQueryResult {
  matchType: 'single' | 'multiple' | 'none';
  message?: string;
  field?: string;
  value?: string;
  record?: Record<string, unknown>;
  count?: number;
  rows?: Record<string, unknown>[];
}

export interface ParsedTask {
  intent: string;
  filters: FilterItem[];
  columns: string[];
}

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  throw new Error('Unexpected response format');
}

export function useCurrentFile() {
  const [current, setCurrent] = useState<FileInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<FileInfo>('/api/files/current')
      .then(data => {
        if (data && (data as any).fileId === null) {
          setCurrent(null);
        } else if (data && data.id) {
          setCurrent(data);
        } else {
          setCurrent(null);
        }
      })
      .catch(() => setCurrent(null))
      .finally(() => setLoading(false));
  }, []);

  const refresh = () => {
    apiRequest<FileInfo>('/api/files/current')
      .then(data => {
        if (data && (data as any).fileId === null) {
          setCurrent(null);
        } else if (data && data.id) {
          setCurrent(data);
        } else {
          setCurrent(null);
        }
      })
      .catch(() => setCurrent(null));
  };

  return { current, loading, refresh };
}

export function useRecentFiles() {
  const [files, setFiles] = useState<FileInfo[]>([]);

  useEffect(() => {
    apiRequest<FileInfo[]>('/api/files/recent')
      .then(data => setFiles(Array.isArray(data) ? data : []))
      .catch(() => setFiles([]));
  }, []);

  const refresh = () => {
    apiRequest<FileInfo[]>('/api/files/recent')
      .then(data => setFiles(Array.isArray(data) ? data : []))
      .catch(() => setFiles([]));
  };

  return { files, refresh };
}

export const fileApi = {
  upload: async (file: File) => {
    const form = new FormData();
    form.append('file', file, file.name);
    const response = await fetch('/api/files/upload', {
      method: 'POST',
      body: form,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || response.statusText);
    }
    return response.json();
  },
  select: (fileId: string) =>
    apiRequest<FileInfo>('/api/files/select', {
      method: 'POST',
      body: JSON.stringify({ fileId }),
    }),
  refresh: (fileId: string) =>
    apiRequest<FileInfo>('/api/files/refresh', {
      method: 'POST',
      body: JSON.stringify({ fileId }),
    }),
};

export const exportApi = {
  preview: (payload: { fileId: string; sheetName?: string | number; filters?: FilterItem[]; columns?: string[] }) =>
    apiRequest<ExportPreviewResult>('/api/export/preview', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  excel: (payload: { fileId: string; sheetName?: string | number; filters?: FilterItem[]; columns?: string[] }) =>
    apiRequest<{ count: number; fileName: string; downloadUrl: string }>('/api/export/excel', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

export const queryApi = {
  quick: (payload: { fileId: string; query: string; sheetName?: string | number }) =>
    apiRequest<QuickQueryResult>('/api/query/quick', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

export const taskApi = {
  parse: (payload: { fileId: string; message: string; sheetName?: string | number; availableColumns?: string[] }) =>
    apiRequest<ParsedTask>('/api/tasks/parse', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  execute: (payload: { fileId: string; sheetName?: string | number; intent: string; filters?: FilterItem[]; columns?: string[] }) =>
    apiRequest<ExportPreviewResult & { fileName?: string; downloadUrl?: string }>('/api/tasks/execute', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
