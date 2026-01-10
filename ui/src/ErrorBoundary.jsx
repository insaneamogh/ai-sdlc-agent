import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null, info: null }
  }

  componentDidCatch(error, info) {
    this.setState({ error, info })
    // also log to console for dev
    console.error('ErrorBoundary caught', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 30, fontFamily: 'monospace', color: '#ff6b6b', background: '#111', minHeight: '100vh' }}>
          <h2 style={{ color: '#ff6b6b' }}>Application Error</h2>
          <div style={{ whiteSpace: 'pre-wrap', marginTop: 12 }}>
            {String(this.state.error && this.state.error.toString())}
          </div>
          <details style={{ marginTop: 12, color: '#999' }}>
            {this.state.info && this.state.info.componentStack}
          </details>
        </div>
      )
    }
    return this.props.children
  }
}
