// @ts-nocheck
import { nav } from '$hangarkit'

export function navigate(path) {
	nav.navigate(path)
	queueMicrotask(() => window.dispatchEvent(new PopStateEvent('popstate')))
}
