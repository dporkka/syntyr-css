# Optional @syntyr/react (unpublished experimental package)

Small typed React components over Syntyr's existing CSS classes.
No runtime state, providers or browser globals. React is a peer dependency.
The package is private until the integration fixtures pass and its API is reviewed.

Build and test: `npm install && npm test`.
Consume via a local file dependency after building; import
`@syntyr/css/core.css` separately from your application entrypoint.

Exports: SyntyrRoot, Button, Card, Badge, Input, Select, Textarea.
These wrappers are optional. Interactive widgets stay in the application,
native HTML, or independently maintained behavior libraries.
