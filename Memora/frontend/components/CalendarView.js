import { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import axios from 'axios';

const CalendarView = () => {
    const [events, setEvents] = useState([]);
    const [todayTasks, setTodayTasks] = useState([]);
    const [stats, setStats] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isClient, setIsClient] = useState(false);

    // Debug logging to understand the mounting sequence
    useEffect(() => {
        console.log('CalendarView: Component mounting, isClient:', typeof window !== 'undefined');
        setIsClient(typeof window !== 'undefined');
        
        if (typeof window !== 'undefined') {
            console.log('CalendarView: Starting fetchTasks immediately');
            fetchTasks();
        }
    }, []);

    const fetchTasks = async () => {
        try {
            console.log('CalendarView: fetchTasks called');
            setError(null);
            setLoading(true);
            
            const [allTasksRes, todayTasksRes, statsRes] = await Promise.all([
                axios.get('http://localhost:8000/tasks'),
                axios.get('http://localhost:8000/tasks/today'),
                axios.get('http://localhost:8000/tasks/stats')
            ]);
            
            console.log('CalendarView: Data fetched successfully', {
                tasks: allTasksRes.data.tasks?.length || 0,
                todayTasks: todayTasksRes.data.tasks?.length || 0,
                stats: statsRes.data
            });

            // Convert tasks to FullCalendar events format
            const calendarEvents = allTasksRes.data.tasks
                .filter(task => {
                    // Filter out tasks with invalid dates
                    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
                    return dateRegex.test(task.date);
                })
                .map(task => ({
                    id: task.id,
                    title: task.title,
                    start: task.start_time ? `${task.date}T${task.start_time}:00` : task.date,
                    end: task.end_time ? `${task.date}T${task.end_time}:00` : task.date,
                    allDay: !task.start_time,
                    backgroundColor: getStatusColor(task.status),
                    borderColor: getPriorityColor(task.priority),
                    extendedProps: {
                        description: task.description,
                        status: task.status,
                        priority: task.priority,
                        startTime: task.start_time,
                        endTime: task.end_time
                    }
                }));

            setEvents(calendarEvents);
            setTodayTasks(todayTasksRes.data.tasks);
            setStats(statsRes.data);
        } catch (error) {
            console.error('CalendarView: Error fetching tasks:', error);
            setError('Failed to load tasks. Make sure the backend server is running.');
        } finally {
            console.log('CalendarView: fetchTasks completed, setting loading to false');
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return '#10B981';
            case 'cancelled': return '#EF4444';
            default: return '#3B82F6';
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return '#DC2626';
            case 'medium': return '#D97706';
            case 'low': return '#059669';
            default: return '#6B7280';
        }
    };

    useEffect(() => {
        if (isClient) {
            // Start fetching data immediately without delay
            fetchTasks();
            // Refresh every 30 seconds
            const interval = setInterval(fetchTasks, 30000);
            return () => clearInterval(interval);
        }
    }, [isClient]);

    // Also fetch data when component mounts, regardless of client state
    useEffect(() => {
        if (typeof window !== 'undefined') {
            fetchTasks();
        }
    }, []);

    const handleEventClick = (clickInfo) => {
        const { title, extendedProps } = clickInfo.event;
        const timeInfo = clickInfo.event.extendedProps.startTime 
            ? `\nTime: ${clickInfo.event.extendedProps.startTime}${clickInfo.event.extendedProps.endTime ? ' - ' + clickInfo.event.extendedProps.endTime : ''}`
            : '';
        
        alert(`📋 ${title}${timeInfo}\n\nDescription: ${extendedProps.description || 'No description'}\nStatus: ${extendedProps.status}\nPriority: ${extendedProps.priority}`);
    };

    // Show basic structure immediately, even if not client-side yet
    console.log('CalendarView: Rendering with isClient:', isClient, 'loading:', loading, 'events:', events.length);
    
    if (!isClient) {
        console.log('CalendarView: Showing non-client state');
        return (
            <div className="p-6 max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold">📅 Schedule Calendar</h1>
                    <span className="text-sm text-red-500">[DEBUG: Not Client-Side]</span>
                </div>
                <div className="flex justify-center items-center h-96">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <p className="text-lg">Loading calendar...</p>
                        <p className="text-sm text-gray-500 mt-2">Setting up your schedule view</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="text-center text-red-600">
                    <p className="text-xl mb-4">⚠️ {error}</p>
                    <button 
                        onClick={fetchTasks}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">📅 Schedule Calendar</h1>
                <button 
                    onClick={fetchTasks}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                >
                    🔄 Refresh
                </button>
            </div>
            
            {/* Stats Section */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
                    <h3 className="text-sm font-medium text-gray-500">Total Tasks</h3>
                    <p className="text-2xl font-bold text-blue-600">{stats.total || 0}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
                    <h3 className="text-sm font-medium text-gray-500">Pending</h3>
                    <p className="text-2xl font-bold text-yellow-600">{stats.pending || 0}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
                    <h3 className="text-sm font-medium text-gray-500">Completed</h3>
                    <p className="text-2xl font-bold text-green-600">{stats.completed || 0}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
                    <h3 className="text-sm font-medium text-gray-500">Today</h3>
                    <p className="text-2xl font-bold text-purple-600">{stats.today || 0}</p>
                </div>
            </div>

            {/* Today's Tasks Section */}
            <div className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">📋 Today's Tasks ({todayTasks.length})</h2>
                {todayTasks.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {todayTasks.map(task => (
                            <div key={task.id} className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
                                <h3 className="font-semibold text-lg">{task.title}</h3>
                                {task.description && (
                                    <p className="text-gray-600 mt-2 text-sm">{task.description}</p>
                                )}
                                <div className="flex justify-between items-center mt-3">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                                        task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                        task.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-red-100 text-red-800'
                                    }`}>
                                        {task.status}
                                    </span>
                                    {task.start_time && (
                                        <span className="text-sm text-gray-500">
                                            {task.start_time}{task.end_time ? ' - ' + task.end_time : ''}
                                        </span>
                                    )}
                                </div>
                                <div className="mt-2">
                                    <span className={`px-2 py-1 rounded text-xs ${
                                        task.priority === 'high' ? 'bg-red-100 text-red-800' :
                                        task.priority === 'medium' ? 'bg-orange-100 text-orange-800' :
                                        'bg-green-100 text-green-800'
                                    }`}>
                                        {task.priority} priority
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-500 italic bg-gray-50 p-4 rounded-lg">
                        📅 No tasks scheduled for today. Use the chat to create some!
                    </p>
                )}
            </div>

            {/* Full Calendar */}
            <div className="bg-white p-6 rounded-lg shadow">
                {isClient ? (
                    <FullCalendar
                        key={`fullcalendar-${events.length}`}
                        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                        headerToolbar={{
                            left: 'prev,next today',
                            center: 'title',
                            right: 'dayGridMonth,timeGridWeek,timeGridDay'
                        }}
                        initialView="dayGridMonth"
                        events={events}
                        eventClick={handleEventClick}
                        height="600px"
                        editable={false}
                        selectable={true}
                        dayMaxEvents={3}
                        eventDisplay="block"
                        eventTimeFormat={{
                            hour: 'numeric',
                            minute: '2-digit',
                            meridiem: false
                        }}
                        loading={(isLoading) => {
                            // Show minimal loading state within FullCalendar
                            if (isLoading && events.length === 0) {
                                return (
                                    <div className="flex justify-center items-center h-96">
                                        <div className="text-center">
                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto mb-2"></div>
                                            <p className="text-sm">Loading events...</p>
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        }}
                    />
                ) : (
                    <div className="h-96 flex flex-col">
                        {/* Show calendar skeleton/placeholder */}
                        <div className="flex justify-between items-center mb-4 p-4 border-b">
                            <div className="flex space-x-2">
                                <div className="w-16 h-8 bg-gray-200 rounded animate-pulse"></div>
                                <div className="w-16 h-8 bg-gray-200 rounded animate-pulse"></div>
                                <div className="w-16 h-8 bg-gray-200 rounded animate-pulse"></div>
                            </div>
                            <div className="w-32 h-8 bg-gray-200 rounded animate-pulse"></div>
                            <div className="flex space-x-2">
                                <div className="w-20 h-8 bg-gray-200 rounded animate-pulse"></div>
                                <div className="w-20 h-8 bg-gray-200 rounded animate-pulse"></div>
                                <div className="w-16 h-8 bg-gray-200 rounded animate-pulse"></div>
                            </div>
                        </div>
                        <div className="grid grid-cols-7 gap-1 flex-1">
                            {Array.from({ length: 35 }).map((_, i) => (
                                <div key={i} className="h-16 bg-gray-50 border border-gray-200 animate-pulse"></div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CalendarView;