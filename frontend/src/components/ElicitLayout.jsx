import { useNavigate } from "react-router-dom";

export default function ElicitLayout({
  children,
  selectedSubject,
  subjects,
  onSubjectChange,
  userId,
}) {
  const navigate = useNavigate();
  const currentPath = window.location.pathname;

  const handleLogout = () => {
    localStorage.removeItem("user_id");
    navigate("/login");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        backgroundColor: "#fafafa",
      }}
    >
      {/* Top Navigation */}
      <div
        style={{
          backgroundColor: "white",
          borderBottom: "1px solid #e5e7eb",
          padding: "12px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: "20px",
            fontWeight: "600",
            color: "#1a1a1a",
          }}
        >
          Question Intelligence
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <span style={{ fontSize: "14px", color: "#6b7280" }}>{userId}</span>
          <button
            onClick={handleLogout}
            style={{
              padding: "6px 16px",
              backgroundColor: "#f3f4f6",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              cursor: "pointer",
              color: "#374151",
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Subject Selector Bar */}
      <div
        style={{
          backgroundColor: "white",
          borderBottom: "1px solid #e5e7eb",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "flex-end",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <label
            style={{ fontSize: "14px", fontWeight: "500", color: "#374151" }}
          >
            Subject:
          </label>
          <select
            value={selectedSubject}
            onChange={(e) => onSubjectChange(e.target.value)}
            style={{
              padding: "8px 16px",
              border: "1px solid #d1d5db",
              borderRadius: "6px",
              fontSize: "14px",
              backgroundColor: "white",
              minWidth: "200px",
            }}
          >
            <option value="">Select Subject</option>
            {subjects.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ display: "flex", flex: 1 }}>
        {/* Left Sidebar */}
        <div
          style={{
            width: "220px",
            backgroundColor: "white",
            borderRight: "1px solid #e5e7eb",
            padding: "24px 16px",
          }}
        >
          <nav style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <button
              onClick={() => navigate("/evaluate")}
              style={{
                padding: "10px 16px",
                textAlign: "left",
                backgroundColor:
                  currentPath === "/evaluate" ? "#f0f9ff" : "transparent",
                border:
                  currentPath === "/evaluate"
                    ? "1px solid #3b82f6"
                    : "1px solid transparent",
                borderRadius: "6px",
                fontSize: "14px",
                cursor: "pointer",
                color: currentPath === "/evaluate" ? "#1e40af" : "#6b7280",
                fontWeight: currentPath === "/evaluate" ? "500" : "400",
              }}
            >
              Evaluate
            </button>
            <button
              onClick={() => navigate("/dashboard")}
              style={{
                padding: "10px 16px",
                textAlign: "left",
                backgroundColor:
                  currentPath === "/dashboard" ? "#f0f9ff" : "transparent",
                border:
                  currentPath === "/dashboard"
                    ? "1px solid #3b82f6"
                    : "1px solid transparent",
                borderRadius: "6px",
                fontSize: "14px",
                cursor: "pointer",
                color: currentPath === "/dashboard" ? "#1e40af" : "#6b7280",
                fontWeight: currentPath === "/dashboard" ? "500" : "400",
              }}
            >
              Subject Setup
            </button>
            <button
              onClick={() => navigate("/history")}
              style={{
                padding: "10px 16px",
                textAlign: "left",
                backgroundColor:
                  currentPath === "/history" ? "#f0f9ff" : "transparent",
                border:
                  currentPath === "/history"
                    ? "1px solid #3b82f6"
                    : "1px solid transparent",
                borderRadius: "6px",
                fontSize: "14px",
                cursor: "pointer",
                color: currentPath === "/history" ? "#1e40af" : "#6b7280",
                fontWeight: currentPath === "/history" ? "500" : "400",
              }}
            >
              History
            </button>
            <button
              onClick={() => navigate("/manage")}
              style={{
                padding: "10px 16px",
                textAlign: "left",
                backgroundColor:
                  currentPath === "/manage" ? "#f0f9ff" : "transparent",
                border:
                  currentPath === "/manage"
                    ? "1px solid #3b82f6"
                    : "1px solid transparent",
                borderRadius: "6px",
                fontSize: "14px",
                cursor: "pointer",
                color: currentPath === "/manage" ? "#1e40af" : "#6b7280",
                fontWeight: currentPath === "/manage" ? "500" : "400",
              }}
            >
              Manage Subjects
            </button>
            {/* <button style={{ padding: '10px 16px', textAlign: 'left', backgroundColor: 'transparent', border: '1px solid transparent', borderRadius: '6px', fontSize: '14px', cursor: 'not-allowed', color: '#9ca3af' }}>
              Saved Papers
            </button> */}
          </nav>
        </div>

        {/* Content Area */}
        <div
          style={{
            flex: 1,
            padding: "32px",
            maxWidth: "1200px",
            margin: "0 auto",
            width: "100%",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
