function Dashboard() {
    const [attendance, setAttendance] = React.useState([]);
    const [analytics, setAnalytics] = React.useState([]);
    const [unauthorized, setUnauthorized] = React.useState([]);
    const [selectedDate, setSelectedDate] = React.useState(new Date().toISOString().split('T')[0]);
    const [systemStatus, setSystemStatus] = React.useState('stopped');

    React.useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [selectedDate]);

    const fetchData = async () => {
        try {
            const [attendanceRes, analyticsRes, unauthorizedRes] = await Promise.all([
                fetch(`/api/attendance?date=${selectedDate}`),
                fetch('/api/analytics'),
                fetch('/api/unauthorized')
            ]);

            setAttendance(await attendanceRes.json());
            setAnalytics(await analyticsRes.json());
            setUnauthorized(await unauthorizedRes.json());
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    const startSystem = async () => {
        try {
            const response = await fetch('/api/start', { method: 'POST' });
            const data = await response.json();
            setSystemStatus('started');
        } catch (error) {
            console.error('Error starting system:', error);
        }
    };

    const stopSystem = async () => {
        try {
            const response = await fetch('/api/stop', { method: 'POST' });
            const data = await response.json();
            setSystemStatus('stopped');
        } catch (error) {
            console.error('Error stopping system:', error);
        }
    };

    const exportData = async (format) => {
        try {
            const response = await fetch(`/api/export?format=${format}&date=${selectedDate}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_${selectedDate}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error exporting data:', error);
        }
    };

    return (
        <div className="container-fluid">
            <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
                <div className="container">
                    <a className="navbar-brand" href="#">Facial Attendance System</a>
                    <div className="d-flex">
                        <button className="btn btn-success me-2" onClick={startSystem} disabled={systemStatus === 'started'}>
                            <i className="bi bi-play-fill"></i> Start
                        </button>
                        <button className="btn btn-danger me-2" onClick={stopSystem} disabled={systemStatus === 'stopped'}>
                            <i className="bi bi-stop-fill"></i> Stop
                        </button>
                        <input
                            type="date"
                            className="form-control me-2"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                        />
                        <div className="btn-group">
                            <button className="btn btn-outline-light" onClick={() => exportData('csv')}>
                                <i className="bi bi-file-earmark-text"></i> CSV
                            </button>
                            <button className="btn btn-outline-light" onClick={() => exportData('excel')}>
                                <i className="bi bi-file-earmark-excel"></i> Excel
                            </button>
                            <button className="btn btn-outline-light" onClick={() => exportData('pdf')}>
                                <i className="bi bi-file-earmark-pdf"></i> PDF
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <div className="container mt-4">
                <div className="row">
                    <div className="col-md-8">
                        <div className="card dashboard-card mb-4">
                            <div className="card-header">
                                <h5 className="card-title mb-0">Today's Attendance</h5>
                            </div>
                            <div className="card-body">
                                <div className="table-responsive">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Time</th>
                                                <th>Camera</th>
                                                <th>Confidence</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {attendance.map((entry, index) => (
                                                <tr key={index}>
                                                    <td>{entry.name}</td>
                                                    <td>{entry.timestamp}</td>
                                                    <td>{entry.camera_id}</td>
                                                    <td>{(entry.confidence * 100).toFixed(2)}%</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="col-md-4">
                        <div className="card dashboard-card mb-4">
                            <div className="card-header">
                                <h5 className="card-title mb-0">Analytics</h5>
                            </div>
                            <div className="card-body">
                                <canvas id="analyticsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="row">
                    <div className="col-12">
                        <div className="card dashboard-card">
                            <div className="card-header">
                                <h5 className="card-title mb-0">Unauthorized Access Attempts</h5>
                            </div>
                            <div className="card-body">
                                <div className="table-responsive">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>Camera</th>
                                                <th>Image</th>
                                                <th>Confidence</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {unauthorized.map((entry, index) => (
                                                <tr key={index}>
                                                    <td>{entry.timestamp}</td>
                                                    <td>{entry.camera_id}</td>
                                                    <td>
                                                        <img
                                                            src={entry.image_path}
                                                            alt="Unauthorized access"
                                                            style={{ maxWidth: '100px' }}
                                                        />
                                                    </td>
                                                    <td>{(entry.confidence * 100).toFixed(2)}%</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<Dashboard />, document.getElementById('root')); 