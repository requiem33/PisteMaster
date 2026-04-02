export const isElectron = (): boolean => {
  return typeof window !== 'undefined' && typeof (window as Window & { electron?: unknown }).electron !== 'undefined'
}

export const isDesktop = isElectron

export const getPlatform = (): 'electron' | 'web' => {
  return isElectron() ? 'electron' : 'web'
}