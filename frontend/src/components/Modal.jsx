export default function Modal({ isOpen, onClose, title, message, type = 'info' }) {
  if (!isOpen) return null;

  const colors = {
    success: { bg: '#d4edda', border: '#c3e6cb', text: '#155724' },
    error: { bg: '#f8d7da', border: '#f5c6cb', text: '#721c24' },
    info: { bg: '#d1ecf1', border: '#bee5eb', text: '#0c5460' },
    warning: { bg: '#fff3cd', border: '#ffeaa7', text: '#856404' }
  };

  const color = colors[type] || colors.info;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }} onClick={onClose}>
      <div style={{
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '8px',
        maxWidth: '500px',
        width: '90%',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }} onClick={(e) => e.stopPropagation()}>
        {title && (
          <h3 style={{
            margin: '0 0 15px 0',
            color: color.text,
            borderBottom: `2px solid ${color.border}`,
            paddingBottom: '10px'
          }}>
            {title}
          </h3>
        )}
        <div style={{
          padding: '15px',
          backgroundColor: color.bg,
          border: `1px solid ${color.border}`,
          borderRadius: '4px',
          color: color.text,
          marginBottom: '20px'
        }}>
          {message}
        </div>
        <button
          onClick={onClose}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px',
            width: '100%'
          }}
        >
          OK
        </button>
      </div>
    </div>
  );
}
