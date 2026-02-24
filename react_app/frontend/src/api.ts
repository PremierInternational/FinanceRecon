import type { CompareResult, ProfilesMap } from './types'

const BASE = '/api'

export async function getColumns(file: File): Promise<string[]> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/columns`, { method: 'POST', body: form })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text)
  }
  const data = await res.json()
  return data.columns as string[]
}

export async function runCompare(
  firstFile: File,
  secondFile: File,
  config: object,
): Promise<CompareResult> {
  const form = new FormData()
  form.append('first_file', firstFile)
  form.append('second_file', secondFile)
  form.append('config', JSON.stringify(config))
  const res = await fetch(`${BASE}/compare`, { method: 'POST', body: form })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text)
  }
  return res.json() as Promise<CompareResult>
}

export function getDownloadUrl(token: string): string {
  return `${BASE}/download/${token}`
}

export async function fetchProfiles(): Promise<ProfilesMap> {
  const res = await fetch(`${BASE}/profiles`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<ProfilesMap>
}

export async function saveProfileApi(name: string, config: object): Promise<void> {
  const res = await fetch(`${BASE}/profiles/${encodeURIComponent(name)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!res.ok) throw new Error(await res.text())
}

export async function deleteProfileApi(name: string): Promise<void> {
  const res = await fetch(`${BASE}/profiles/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(await res.text())
}
