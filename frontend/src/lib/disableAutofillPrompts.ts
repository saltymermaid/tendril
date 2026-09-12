/**
 * Dashlane (and similar password managers) inject autofill icons/pickers into
 * form fields app-wide, including date inputs, which makes no sense for a
 * garden planner. These are the vendor-documented opt-out attributes;
 * applying them to every field (and re-applying as new fields mount, e.g. in
 * modals) suppresses that UI everywhere.
 */
const IGNORE_ATTRS: Record<string, string> = {
  'data-dashlane-ignore': 'true',
  'data-form-type': 'other',
  autocomplete: 'off',
}

function tagField(el: Element) {
  for (const [attr, value] of Object.entries(IGNORE_ATTRS)) {
    if (!el.hasAttribute(attr)) el.setAttribute(attr, value)
  }
}

function tagAllFields(root: ParentNode) {
  root.querySelectorAll('input, select, textarea, form').forEach(tagField)
}

export function disableAutofillPrompts() {
  tagAllFields(document)

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof Element)) return
        if (node.matches('input, select, textarea, form')) tagField(node)
        tagAllFields(node)
      })
    }
  })
  observer.observe(document.body, { childList: true, subtree: true })

  return () => observer.disconnect()
}
