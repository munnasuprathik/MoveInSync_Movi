import React, { useState, useEffect } from 'react'
import { tripsAPI, deploymentsAPI, vehiclesAPI, driversAPI, routesAPI } from '../services/api'
import { dataCache } from '../utils/dataCache'
import './BusDashboard.css'

function BusDashboard() {
  const [trips, setTrips] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [drivers, setDrivers] = useState([])
  const [routes, setRoutes] = useState([])
  const [deployments, setDeployments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  
  // Vehicle modals
  const [showAddVehicleModal, setShowAddVehicleModal] = useState(false)
  const [showEditVehicleModal, setShowEditVehicleModal] = useState(false)
  const [editingVehicle, setEditingVehicle] = useState(null)
  const [vehicleFormData, setVehicleFormData] = useState({
    license_plate: '',
    type: 'Bus',
    capacity: '',
    make: '',
    model: '',
    year: '',
    color: '',
    is_available: true,
    status: 'active',
    notes: ''
  })
  
  // Driver modals
  const [showAddDriverModal, setShowAddDriverModal] = useState(false)
  const [showEditDriverModal, setShowEditDriverModal] = useState(false)
  const [editingDriver, setEditingDriver] = useState(null)
  const [driverFormData, setDriverFormData] = useState({
    name: '',
    phone_number: '',
    email: '',
    license_number: '',
    is_available: true,
    status: 'active',
    notes: ''
  })
  
  // Trip modal
  const [showAddTripModal, setShowAddTripModal] = useState(false)
  const [tripFormData, setTripFormData] = useState({
    route_id: '',
    display_name: '',
    trip_date: '',
    booking_status_percentage: 0,
    live_status: '',
    total_bookings: 0,
    status: 'scheduled',
    notes: ''
  })

  useEffect(() => {
    loadAllData()
  }, [])

  const loadAllData = async (forceRefresh = false) => {
    try {
      setLoading(true)
      
      // Check cache first (unless forcing refresh)
      if (!forceRefresh) {
        const cachedTrips = dataCache.get('trips')
        const cachedVehicles = dataCache.get('vehicles')
        const cachedDrivers = dataCache.get('drivers')
        const cachedRoutes = dataCache.get('routes')
        const cachedDeployments = dataCache.get('deployments')
        
        if (cachedTrips && cachedVehicles && cachedDrivers && cachedRoutes && cachedDeployments) {
          setTrips(cachedTrips)
          setVehicles(cachedVehicles)
          setDrivers(cachedDrivers)
          setRoutes(cachedRoutes)
          setDeployments(cachedDeployments)
          setLoading(false)
          return
        }
      }
      
      // Load all data in parallel (including all deployments at once)
      const [tripsRes, vehiclesRes, driversRes, routesRes, deploymentsRes] = await Promise.all([
        tripsAPI.getAll(),
        vehiclesAPI.getAll(),
        driversAPI.getAll(),
        routesAPI.getAll(),
        deploymentsAPI.getAll()
      ])
      
      // Update state
      setTrips(tripsRes.data)
      setVehicles(vehiclesRes.data)
      setDrivers(driversRes.data)
      setRoutes(routesRes.data)
      setDeployments(deploymentsRes.data || [])
      
      // Update cache
      dataCache.set('trips', tripsRes.data)
      dataCache.set('vehicles', vehiclesRes.data)
      dataCache.set('drivers', driversRes.data)
      dataCache.set('routes', routesRes.data)
      dataCache.set('deployments', deploymentsRes.data || [])
      
      setError(null)
    } catch (err) {
      setError('Failed to load data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadTrips = async () => {
    try {
      // Reload all data including deployments
      await loadAllData(true)
    } catch (err) {
      setError('Failed to load trips')
      console.error(err)
    }
  }

  const handleCreateVehicle = async () => {
    try {
      if (!vehicleFormData.license_plate || !vehicleFormData.capacity) {
        alert('Please fill in all required fields (License Plate and Capacity)')
        return
      }

      await vehiclesAPI.create({
        ...vehicleFormData,
        capacity: parseInt(vehicleFormData.capacity),
        year: vehicleFormData.year ? parseInt(vehicleFormData.year) : null,
      })
      
      dataCache.clear('vehicles')
      await loadAllData(true)
      
      setVehicleFormData({
        license_plate: '',
        type: 'Bus',
        capacity: '',
        make: '',
        model: '',
        year: '',
        color: '',
        is_available: true,
        status: 'active',
        notes: ''
      })
      setShowAddVehicleModal(false)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create bus'
      alert(errorMsg)
      console.error(err)
    }
  }

  const handleEditVehicle = (vehicle) => {
    setEditingVehicle(vehicle)
    setVehicleFormData({
      license_plate: vehicle.license_plate || '',
      type: vehicle.type || 'Bus',
      capacity: vehicle.capacity || '',
      make: vehicle.make || '',
      model: vehicle.model || '',
      year: vehicle.year || '',
      color: vehicle.color || '',
      is_available: vehicle.is_available !== undefined ? vehicle.is_available : true,
      status: vehicle.status || 'active',
      notes: vehicle.notes || ''
    })
    setShowEditVehicleModal(true)
  }

  const handleUpdateVehicle = async () => {
    try {
      if (!vehicleFormData.license_plate || !vehicleFormData.capacity) {
        alert('Please fill in all required fields')
        return
      }

      await vehiclesAPI.update(editingVehicle.vehicle_id, {
        ...vehicleFormData,
        capacity: parseInt(vehicleFormData.capacity),
        year: vehicleFormData.year ? parseInt(vehicleFormData.year) : null,
      })
      
      dataCache.clear('vehicles')
      await loadAllData(true)
      
      setShowEditVehicleModal(false)
      setEditingVehicle(null)
      setVehicleFormData({
        license_plate: '',
        type: 'Bus',
        capacity: '',
        make: '',
        model: '',
        year: '',
        color: '',
        is_available: true,
        status: 'active',
        notes: ''
      })
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to update vehicle'
      alert(errorMsg)
      console.error(err)
    }
  }

  const handleDeleteVehicle = async (vehicleId, licensePlate) => {
    if (window.confirm(`Are you sure you want to delete vehicle "${licensePlate}"?`)) {
      try {
        await vehiclesAPI.delete(vehicleId, 1)
        dataCache.clear('vehicles')
        await loadAllData(true)
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete vehicle'
        alert(errorMsg)
        console.error(err)
      }
    }
  }

  const handleCreateDriver = async () => {
    try {
      if (!driverFormData.name || !driverFormData.phone_number) {
        alert('Please fill in all required fields (Name and Phone Number)')
        return
      }

      await driversAPI.create(driverFormData)
      
      dataCache.clear('drivers')
      await loadAllData(true)
      
      setDriverFormData({
        name: '',
        phone_number: '',
        email: '',
        license_number: '',
        is_available: true,
        status: 'active',
        notes: ''
      })
      setShowAddDriverModal(false)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create driver'
      alert(errorMsg)
      console.error(err)
    }
  }

  const handleEditDriver = (driver) => {
    setEditingDriver(driver)
    setDriverFormData({
      name: driver.name || '',
      phone_number: driver.phone_number || '',
      email: driver.email || '',
      license_number: driver.license_number || '',
      is_available: driver.is_available !== undefined ? driver.is_available : true,
      status: driver.status || 'active',
      notes: driver.notes || ''
    })
    setShowEditDriverModal(true)
  }

  const handleUpdateDriver = async () => {
    try {
      if (!driverFormData.name || !driverFormData.phone_number) {
        alert('Please fill in all required fields')
        return
      }

      await driversAPI.update(editingDriver.driver_id, driverFormData)
      
      dataCache.clear('drivers')
      await loadAllData(true)
      
      setShowEditDriverModal(false)
      setEditingDriver(null)
      setDriverFormData({
        name: '',
        phone_number: '',
        email: '',
        license_number: '',
        is_available: true,
        status: 'active',
        notes: ''
      })
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to update driver'
      alert(errorMsg)
      console.error(err)
    }
  }

  const handleDeleteDriver = async (driverId, driverName) => {
    if (window.confirm(`Are you sure you want to delete driver "${driverName}"?`)) {
      try {
        await driversAPI.delete(driverId, 1)
        dataCache.clear('drivers')
        await loadAllData(true)
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete driver'
        alert(errorMsg)
        console.error(err)
      }
    }
  }

  const handleCreateTrip = async () => {
    try {
      if (!tripFormData.route_id || !tripFormData.display_name || !tripFormData.trip_date) {
        alert('Please fill in all required fields (Route, Display Name, and Trip Date)')
        return
      }

      await tripsAPI.create({
        ...tripFormData,
        route_id: parseInt(tripFormData.route_id),
        trip_date: tripFormData.trip_date,
        booking_status_percentage: parseFloat(tripFormData.booking_status_percentage) || 0,
        total_bookings: parseInt(tripFormData.total_bookings) || 0,
      })
      
      dataCache.clear('trips')
      await loadAllData(true)
      
      setTripFormData({
        route_id: '',
        display_name: '',
        trip_date: '',
        booking_status_percentage: 0,
        live_status: '',
        total_bookings: 0,
        status: 'scheduled',
        notes: ''
      })
      setShowAddTripModal(false)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create trip'
      alert(errorMsg)
      console.error(err)
    }
  }

  const filteredTrips = trips.filter(trip => {
    const matchesSearch = trip.display_name?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || trip.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const stats = {
    total: trips.length,
    scheduled: trips.filter(t => t.status === 'scheduled').length,
    inProgress: trips.filter(t => t.status === 'in_progress').length,
    completed: trips.filter(t => t.status === 'completed').length,
  }

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading trips...</p>
      </div>
    )
  }

  if (error) {
    return <div className="dashboard-error">{error}</div>
  }

  return (
    <div className="bus-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>Bus Dashboard</h1>
          <p className="subtitle">Manage trips and deployments</p>
        </div>
        <div className="header-actions">
          <button onClick={() => setShowAddVehicleModal(true)} className="add-vehicle-btn">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 3V17M3 10H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Add Bus
          </button>
          <button onClick={() => loadAllData(true)} className="refresh-btn">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M17.5 10C17.5 14.1421 14.1421 17.5 10 17.5M17.5 10C17.5 5.85786 14.1421 2.5 10 2.5M17.5 10H2.5M2.5 10C2.5 5.85786 5.85786 2.5 10 2.5M2.5 10C2.5 14.1421 5.85786 17.5 10 17.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' }}>
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L2 7L10 12L18 7L10 2Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 13L10 18L18 13" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">Total Trips</p>
            <p className="stat-value">{stats.total}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' }}>
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L2 7L10 12L18 7L10 2Z" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">Scheduled</p>
            <p className="stat-value">{stats.scheduled}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="8" stroke="white" strokeWidth="1.5"/>
              <path d="M10 6V10L13 13" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">In Progress</p>
            <p className="stat-value">{stats.inProgress}</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none">
              <path d="M16 6L8 14L4 10" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="stat-content">
            <p className="stat-label">Completed</p>
            <p className="stat-value">{stats.completed}</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-box">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M14 14L17 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <input
            type="text"
            placeholder="Search trips..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Status</option>
          <option value="scheduled">Scheduled</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Trips Grid */}
      <div className="trips-section">
        <div className="section-header-inline">
          <h2 className="section-title">Trips</h2>
          <button onClick={() => setShowAddTripModal(true)} className="add-btn-small">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
              <path d="M10 3V17M3 10H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Add Trip
          </button>
        </div>
        {filteredTrips.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L2 7L10 12L18 7L10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <p>No trips found</p>
          </div>
        ) : (
          <div className="trips-grid">
            {filteredTrips.map((trip) => (
              <TripCard 
                key={trip.trip_id} 
                trip={trip} 
                vehicles={vehicles}
                drivers={drivers}
                deployments={deployments}
                onRefresh={loadTrips} 
              />
            ))}
          </div>
        )}
      </div>

      {/* Add Vehicle Modal */}
      {showAddVehicleModal && (
        <div className="modal-overlay" onClick={() => setShowAddVehicleModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Add New Bus</h3>
            <div className="modal-form">
              <label>
                License Plate *
                <input
                  type="text"
                  value={vehicleFormData.license_plate}
                  onChange={(e) => setVehicleFormData({ ...vehicleFormData, license_plate: e.target.value })}
                  placeholder="e.g., KA-01-AB-1234"
                  required
                />
              </label>
              <label>
                Type *
                <select
                  value={vehicleFormData.type}
                  onChange={(e) => setVehicleFormData({ ...vehicleFormData, type: e.target.value })}
                  required
                >
                  <option value="Bus">Bus</option>
                  <option value="Cab">Cab</option>
                </select>
              </label>
              <label>
                Capacity *
                <input
                  type="number"
                  value={vehicleFormData.capacity}
                  onChange={(e) => setVehicleFormData({ ...vehicleFormData, capacity: e.target.value })}
                  placeholder="Number of seats"
                  min="1"
                  required
                />
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <label>
                  Make
                  <input
                    type="text"
                    value={vehicleFormData.make}
                    onChange={(e) => setVehicleFormData({ ...vehicleFormData, make: e.target.value })}
                    placeholder="e.g., Tata"
                  />
                </label>
                <label>
                  Model
                  <input
                    type="text"
                    value={vehicleFormData.model}
                    onChange={(e) => setVehicleFormData({ ...vehicleFormData, model: e.target.value })}
                    placeholder="e.g., Starbus"
                  />
                </label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <label>
                  Year
                  <input
                    type="number"
                    value={vehicleFormData.year}
                    onChange={(e) => setVehicleFormData({ ...vehicleFormData, year: e.target.value })}
                    placeholder="e.g., 2023"
                    min="1900"
                    max={new Date().getFullYear() + 1}
                  />
                </label>
                <label>
                  Color
                  <input
                    type="text"
                    value={vehicleFormData.color}
                    onChange={(e) => setVehicleFormData({ ...vehicleFormData, color: e.target.value })}
                    placeholder="e.g., Blue"
                  />
                </label>
              </div>
              <label>
                Status *
                <select
                  value={vehicleFormData.status}
                  onChange={(e) => setVehicleFormData({ ...vehicleFormData, status: e.target.value })}
                  required
                >
                  <option value="active">Active</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="retired">Retired</option>
                </select>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={vehicleFormData.is_available}
                  onChange={(e) => setVehicleFormData({ ...vehicleFormData, is_available: e.target.checked })}
                />
                <span>Available for assignment</span>
              </label>
              <label>
                Notes
                <textarea
                  value={vehicleFormData.notes}
                  onChange={(e) => setVehicleFormData({ ...vehicleFormData, notes: e.target.value })}
                  placeholder="Additional notes about the vehicle"
                  rows="3"
                />
              </label>
              <div className="modal-actions">
                <button onClick={handleCreateVehicle} className="btn-primary">Create Bus</button>
                <button onClick={() => {
                  setShowAddVehicleModal(false)
                  setVehicleFormData({
                    license_plate: '',
                    type: 'Bus',
                    capacity: '',
                    make: '',
                    model: '',
                    year: '',
                    color: '',
                    is_available: true,
                    status: 'active',
                    notes: ''
                  })
                }} className="btn-secondary">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Trip Modal */}
      {showAddTripModal && (
        <div className="modal-overlay" onClick={() => setShowAddTripModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Create New Trip</h3>
            <div className="modal-form">
              <label>
                Route *
                <select
                  value={tripFormData.route_id}
                  onChange={(e) => setTripFormData({ ...tripFormData, route_id: e.target.value })}
                  required
                >
                  <option value="">Select Route</option>
                  {routes.map(r => (
                    <option key={r.route_id} value={r.route_id}>
                      {r.route_display_name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Display Name *
                <input
                  type="text"
                  value={tripFormData.display_name}
                  onChange={(e) => setTripFormData({ ...tripFormData, display_name: e.target.value })}
                  placeholder="e.g., ROUTE-EC-001-2024-01-15"
                  required
                />
              </label>
              <label>
                Trip Date *
                <input
                  type="date"
                  value={tripFormData.trip_date}
                  onChange={(e) => setTripFormData({ ...tripFormData, trip_date: e.target.value })}
                  required
                />
              </label>
              <label>
                Status *
                <select
                  value={tripFormData.status}
                  onChange={(e) => setTripFormData({ ...tripFormData, status: e.target.value })}
                  required
                >
                  <option value="scheduled">Scheduled</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <label>
                  Booking %
                  <input
                    type="number"
                    value={tripFormData.booking_status_percentage}
                    onChange={(e) => setTripFormData({ ...tripFormData, booking_status_percentage: e.target.value })}
                    min="0"
                    max="100"
                    step="0.1"
                    placeholder="0"
                  />
                </label>
                <label>
                  Total Bookings
                  <input
                    type="number"
                    value={tripFormData.total_bookings}
                    onChange={(e) => setTripFormData({ ...tripFormData, total_bookings: e.target.value })}
                    min="0"
                    placeholder="0"
                  />
                </label>
              </div>
              <label>
                Live Status
                <input
                  type="text"
                  value={tripFormData.live_status}
                  onChange={(e) => setTripFormData({ ...tripFormData, live_status: e.target.value })}
                  placeholder="e.g., 08:00 OUT"
                />
              </label>
              <label>
                Notes
                <textarea
                  value={tripFormData.notes}
                  onChange={(e) => setTripFormData({ ...tripFormData, notes: e.target.value })}
                  placeholder="Additional notes about the trip"
                  rows="3"
                />
              </label>
              <div className="modal-actions">
                <button onClick={handleCreateTrip} className="btn-primary">Create Trip</button>
                <button 
                  onClick={() => {
                    setShowAddTripModal(false)
                    setTripFormData({
                      route_id: '',
                      display_name: '',
                      trip_date: '',
                      booking_status_percentage: 0,
                      live_status: '',
                      total_bookings: 0,
                      status: 'scheduled',
                      notes: ''
                    })
                  }} 
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TripCard({ trip, vehicles, drivers, deployments, onRefresh }) {
  const [deployment, setDeployment] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showEditDriverModal, setShowEditDriverModal] = useState(false)
  const [vehicleDetails, setVehicleDetails] = useState(null)
  const [driverDetails, setDriverDetails] = useState(null)
  const [assignData, setAssignData] = useState({ vehicle_id: '', driver_id: '' })
  const [editData, setEditData] = useState({ status: trip.status, live_status: trip.live_status || '' })
  const [driverEditData, setDriverEditData] = useState({
    name: '',
    phone_number: '',
    email: '',
    license_number: '',
    is_available: true,
    status: 'active'
  })

  useEffect(() => {
    // Find deployment from the pre-loaded deployments array (much faster!)
    const tripDeployment = deployments.find(d => d.trip_id === trip.trip_id)
    setDeployment(tripDeployment || null)
    
    // Load vehicle and driver details if deployment exists
    if (tripDeployment) {
      // Use cached vehicles/drivers
      const vehicle = vehicles.find(v => v.vehicle_id === tripDeployment.vehicle_id)
      const driver = drivers.find(d => d.driver_id === tripDeployment.driver_id)
      
      setVehicleDetails(vehicle || null)
      setDriverDetails(driver || null)
    } else {
      setVehicleDetails(null)
      setDriverDetails(null)
    }
  }, [trip.trip_id, deployments, vehicles, drivers])

  const handleAssign = async () => {
    try {
      if (deployment) {
        await deploymentsAPI.update(deployment.deployment_id, {
          vehicle_id: parseInt(assignData.vehicle_id),
          driver_id: parseInt(assignData.driver_id),
          deployment_status: 'assigned',
        })
      } else {
        await deploymentsAPI.create({
          trip_id: trip.trip_id,
          vehicle_id: parseInt(assignData.vehicle_id),
          driver_id: parseInt(assignData.driver_id),
          deployment_status: 'assigned',
        })
      }
      setShowAssignModal(false)
      setAssignData({ vehicle_id: '', driver_id: '' })
      // Clear cache and reload all data
      dataCache.clear('trips')
      dataCache.clear('deployments')
      onRefresh()
    } catch (err) {
      alert('Failed to assign vehicle/driver')
      console.error(err)
    }
  }

  const handleRemove = async () => {
    if (window.confirm('Are you sure you want to remove the vehicle assignment?')) {
      try {
        if (deployment) {
          await deploymentsAPI.delete(deployment.deployment_id, 1)
          setDeployment(null)
          // Clear cache since deployment was removed
          dataCache.clear('trips')
          dataCache.clear('deployments')
          onRefresh()
        }
      } catch (err) {
        alert('Failed to remove vehicle')
        console.error(err)
      }
    }
  }

  const handleEditStatus = async () => {
    try {
      await tripsAPI.update(trip.trip_id, editData)
      setShowEditModal(false)
      // Clear cache since trip was updated
      dataCache.clear('trips')
      dataCache.clear('deployments')
      onRefresh()
    } catch (err) {
      alert('Failed to update trip status')
      console.error(err)
    }
  }

  const handleEditDriver = () => {
    if (driverDetails) {
      setDriverEditData({
        name: driverDetails.name || '',
        phone_number: driverDetails.phone_number || '',
        email: driverDetails.email || '',
        license_number: driverDetails.license_number || '',
        is_available: driverDetails.is_available !== undefined ? driverDetails.is_available : true,
        status: driverDetails.status || 'active'
      })
      setShowEditDriverModal(true)
    }
  }

  const handleUpdateDriver = async () => {
    try {
      if (driverDetails) {
        await driversAPI.update(driverDetails.driver_id, driverEditData)
        setShowEditDriverModal(false)
        // Reload driver details
        const driverRes = await driversAPI.getById(driverDetails.driver_id)
        setDriverDetails(driverRes.data)
        // Clear drivers cache so it refreshes on next load
        dataCache.clear('drivers')
        onRefresh()
      }
    } catch (err) {
      alert('Failed to update driver information')
      console.error(err)
    }
  }

  const handleDeleteTrip = async () => {
    if (window.confirm(`Are you sure you want to delete trip "${trip.display_name}"? This action cannot be undone.`)) {
      try {
        await tripsAPI.delete(trip.trip_id, 1)
        // Clear cache and reload all data
        dataCache.clear('trips')
        dataCache.clear('deployments')
        onRefresh()
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete trip'
        alert(errorMsg)
        console.error(err)
      }
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      scheduled: '#3b82f6',
      in_progress: '#f59e0b',
      completed: '#10b981',
      cancelled: '#ef4444',
    }
    return colors[status] || '#6b7280'
  }

  return (
    <>
      <div className="trip-card">
        <div className="trip-card-header">
          <div>
            <h3>{trip.display_name}</h3>
            <p className="trip-date">{trip.trip_date}</p>
          </div>
          <span 
            className="status-badge" 
            style={{ backgroundColor: `${getStatusColor(trip.status)}20`, color: getStatusColor(trip.status) }}
          >
            {trip.status.replace('_', ' ')}
          </span>
        </div>

        <div className="trip-details">
          <div className="detail-item">
            <span className="detail-label">Bookings</span>
            <span className="detail-value">{trip.booking_status_percentage}%</span>
          </div>
          {trip.live_status && (
            <div className="detail-item">
              <span className="detail-label">Live Status</span>
              <span className="detail-value">{trip.live_status}</span>
            </div>
          )}
        </div>

        {loading ? (
          <div className="deployment-loading">Loading...</div>
        ) : deployment ? (
          <div className="deployment-section">
            <div className="deployment-info">
              <div className="deployment-item">
                <span className="deployment-label">Vehicle:</span>
                <span className="deployment-value">
                  {vehicleDetails ? (
                    <strong>{vehicleDetails.license_plate}</strong>
                  ) : (
                    `ID: ${deployment.vehicle_id}`
                  )}
                </span>
              </div>
              <div className="deployment-item">
                <span className="deployment-label">Driver:</span>
                <span className="deployment-value">
                  {driverDetails ? (
                    <div className="driver-info">
                      <strong>{driverDetails.name}</strong>
                      <button 
                        onClick={handleEditDriver} 
                        className="edit-driver-btn"
                        title="Edit driver information"
                      >
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                          <path d="M11 3H5C4.46957 3 3.96086 3.21071 3.58579 3.58579C3.21071 3.96086 3 4.46957 3 5V15C3 15.5304 3.21071 16.0391 3.58579 16.4142C3.96086 16.7893 4.46957 17 5 17H15C15.5304 17 16.0391 16.7893 16.4142 16.4142C16.7893 16.0391 17 15.5304 17 15V9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                          <path d="M14.5 2.5C14.7652 2.23478 15.1159 2.1096 15.5 2.1096C15.8841 2.1096 16.2348 2.23478 16.5 2.5C16.7652 2.76522 16.8904 3.11593 16.8904 3.5C16.8904 3.88407 16.7652 4.23478 16.5 4.5L10 11L7 12L8 9L14.5 2.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>
                  ) : (
                    `ID: ${deployment.driver_id}`
                  )}
                </span>
              </div>
              {driverDetails && (
                <div className="deployment-item driver-details">
                  <span className="deployment-label">Contact:</span>
                  <span className="deployment-value">{driverDetails.phone_number}</span>
                </div>
              )}
              <div className="deployment-item">
                <span className="deployment-label">Status:</span>
                <span className="deployment-value">
                  <strong>{deployment.deployment_status.replace('_', ' ')}</strong>
                </span>
              </div>
            </div>
            <div className="card-actions">
              <button onClick={() => setShowAssignModal(true)} className="btn-primary">
                Reassign
              </button>
              <button onClick={handleRemove} className="btn-danger">
                Remove
              </button>
            </div>
          </div>
        ) : (
          <div className="no-deployment">
            <p>No vehicle assigned</p>
            <button onClick={() => setShowAssignModal(true)} className="btn-primary">
              Assign Vehicle & Driver
            </button>
          </div>
        )}

        <div className="card-actions">
          <button onClick={() => setShowEditModal(true)} className="btn-secondary">
            Edit Status
          </button>
          <button onClick={handleDeleteTrip} className="btn-danger">
            Delete Trip
          </button>
        </div>
      </div>

      {/* Assign Modal */}
      {showAssignModal && (
        <div className="modal-overlay" onClick={() => setShowAssignModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Assign Vehicle & Driver</h3>
            <div className="modal-form">
              <label>
                Vehicle
                <select
                  value={assignData.vehicle_id}
                  onChange={(e) => setAssignData({ ...assignData, vehicle_id: e.target.value })}
                  required
                >
                  <option value="">Select Vehicle</option>
                  {vehicles.map(v => (
                    <option key={v.vehicle_id} value={v.vehicle_id}>
                      {v.license_plate} - {v.type} ({v.capacity} seats)
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Driver
                <select
                  value={assignData.driver_id}
                  onChange={(e) => setAssignData({ ...assignData, driver_id: e.target.value })}
                  required
                >
                  <option value="">Select Driver</option>
                  {drivers.map(d => (
                    <option key={d.driver_id} value={d.driver_id}>
                      {d.name} - {d.phone_number}
                    </option>
                  ))}
                </select>
              </label>
              <div className="modal-actions">
                <button onClick={handleAssign} className="btn-primary">Assign</button>
                <button onClick={() => setShowAssignModal(false)} className="btn-secondary">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Status Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Trip Status</h3>
            <div className="modal-form">
              <label>
                Status
                <select
                  value={editData.status}
                  onChange={(e) => setEditData({ ...editData, status: e.target.value })}
                >
                  <option value="scheduled">Scheduled</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </label>
              <label>
                Live Status
                <input
                  type="text"
                  value={editData.live_status}
                  onChange={(e) => setEditData({ ...editData, live_status: e.target.value })}
                  placeholder="e.g., 08:00 OUT"
                />
              </label>
              <div className="modal-actions">
                <button onClick={handleEditStatus} className="btn-primary">Update</button>
                <button onClick={() => setShowEditModal(false)} className="btn-secondary">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Driver Modal */}
      {showEditDriverModal && driverDetails && (
        <div className="modal-overlay" onClick={() => setShowEditDriverModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Driver Information</h3>
            <div className="modal-form">
              <label>
                Driver Name
                <input
                  type="text"
                  value={driverEditData.name}
                  onChange={(e) => setDriverEditData({ ...driverEditData, name: e.target.value })}
                  required
                />
              </label>
              <label>
                Phone Number
                <input
                  type="text"
                  value={driverEditData.phone_number}
                  onChange={(e) => setDriverEditData({ ...driverEditData, phone_number: e.target.value })}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={driverEditData.email}
                  onChange={(e) => setDriverEditData({ ...driverEditData, email: e.target.value })}
                />
              </label>
              <label>
                License Number
                <input
                  type="text"
                  value={driverEditData.license_number}
                  onChange={(e) => setDriverEditData({ ...driverEditData, license_number: e.target.value })}
                  required
                />
              </label>
              <label>
                Status
                <select
                  value={driverEditData.status}
                  onChange={(e) => setDriverEditData({ ...driverEditData, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={driverEditData.is_available}
                  onChange={(e) => setDriverEditData({ ...driverEditData, is_available: e.target.checked })}
                />
                <span>Available</span>
              </label>
              <div className="modal-actions">
                <button onClick={handleUpdateDriver} className="btn-primary">Update Driver</button>
                <button onClick={() => setShowEditDriverModal(false)} className="btn-secondary">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default BusDashboard
