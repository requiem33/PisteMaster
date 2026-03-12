const CSRF_COOKIE_NAME = 'csrftoken'
const CSRF_HEADER_NAME = 'X-CSRFToken'

function getCookie(name: string): string | null {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) {
        return parts.pop()?.split(';').shift() || null
    }
    return null
}

export function getCsrfToken(): string | null {
    return getCookie(CSRF_COOKIE_NAME)
}

export function getCsrfHeaders(): Record<string, string> {
    const token = getCsrfToken()
    if (token) {
        return { [CSRF_HEADER_NAME]: token }
    }
    return {}
}

export function getApiHeaders(includeCsrf: boolean = true): Record<string, string> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    }
    if (includeCsrf) {
        Object.assign(headers, getCsrfHeaders())
    }
    return headers
}
