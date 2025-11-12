import React, { useState, useEffect } from 'react'
import { stopsAPI, pathsAPI, routesAPI } from '../services/api'
import { dataCache } from '../utils/dataCache'
import './ManageRoute.css'

function ManageRoute() {
  const [activeTab, setActiveTab] = useState('stops')
  const [stops, setStops] = useState([])
  const [paths, setPaths] = useState([])
  const [routes, setRoutes] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async (forceRefresh = false) => {
    setLoading(true)
    try {
      // Check cache first (unless forcing refresh)
      if (!forceRefresh) {
        const cachedStops = dataCache.get('stops')
        const cachedPaths = dataCache.get('paths')
        const cachedRoutes = dataCache.get('routes')
        
        if (cachedStops && cachedPaths && cachedRoutes) {
          setStops(cachedStops)
          setPaths(cachedPaths)
          setRoutes(cachedRoutes)
          setLoading(false)
          return
        }
      }
      
      const [stopsRes, pathsRes, routesRes] = await Promise.all([
        stopsAPI.getAll(),
        pathsAPI.getAll(),
        routesAPI.getAll(),
      ])
      setStops(stopsRes.data)
      setPaths(pathsRes.data)
      setRoutes(routesRes.data)
      
      // Update cache
      dataCache.set('stops', stopsRes.data)
      dataCache.set('paths', pathsRes.data)
      dataCache.set('routes', routesRes.data)
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="manage-route">
      <div className="page-header">
        <div>
          <h1>Manage Route</h1>
          <p className="subtitle">Manage stops, paths, and routes</p>
        </div>
      </div>

      <div className="tabs">
        <button
          className={activeTab === 'stops' ? 'active' : ''}
          onClick={() => setActiveTab('stops')}
        >
          Stops
        </button>
        <button
          className={activeTab === 'paths' ? 'active' : ''}
          onClick={() => setActiveTab('paths')}
        >
          Paths
        </button>
        <button
          className={activeTab === 'routes' ? 'active' : ''}
          onClick={() => setActiveTab('routes')}
        >
          Routes
        </button>
      </div>

      <div className="tab-content">
        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <>
            {activeTab === 'stops' && <StopsTab stops={stops} onRefresh={() => loadData(true)} />}
            {activeTab === 'paths' && <PathsTab paths={paths} stops={stops} onRefresh={() => loadData(true)} />}
            {activeTab === 'routes' && <RoutesTab routes={routes} paths={paths} onRefresh={() => loadData(true)} />}
          </>
        )}
      </div>
    </div>
  )
}

function StopsTab({ stops, onRefresh }) {
  const [showForm, setShowForm] = useState(false)
  const [editingStop, setEditingStop] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    latitude: '',
    longitude: '',
    description: '',
    address: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingStop) {
        await stopsAPI.update(editingStop.stop_id, {
          ...formData,
          latitude: parseFloat(formData.latitude),
          longitude: parseFloat(formData.longitude),
        })
      } else {
        await stopsAPI.create({
          ...formData,
          latitude: parseFloat(formData.latitude),
          longitude: parseFloat(formData.longitude),
        })
      }
      setShowForm(false)
      setEditingStop(null)
      setFormData({ name: '', latitude: '', longitude: '', description: '', address: '' })
      onRefresh()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || `Failed to ${editingStop ? 'update' : 'create'} stop`
      alert(errorMsg)
      console.error(err)
    }
  }

  const handleEdit = (stop) => {
    setEditingStop(stop)
    setFormData({
      name: stop.name || '',
      latitude: stop.latitude || '',
      longitude: stop.longitude || '',
      description: stop.description || '',
      address: stop.address || '',
    })
    setShowForm(true)
  }

  const handleDelete = async (stopId) => {
    if (window.confirm('Are you sure you want to delete this stop?')) {
      try {
        await stopsAPI.delete(stopId, 1) // deleted_by = 1 (admin)
        onRefresh()
      } catch (err) {
        alert('Failed to delete stop')
        console.error(err)
      }
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingStop(null)
    setFormData({ name: '', latitude: '', longitude: '', description: '', address: '' })
  }

  return (
    <div className="stops-tab">
      <div className="section-header">
        <h2>Stops</h2>
        <button onClick={() => setShowForm(!showForm)} className="add-btn">
          {showForm ? 'Cancel' : '+ Add Stop'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="form">
          <h3>{editingStop ? 'Edit Stop' : 'Create New Stop'}</h3>
          <input
            type="text"
            placeholder="Stop Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <input
            type="number"
            step="any"
            placeholder="Latitude"
            value={formData.latitude}
            onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
            required
          />
          <input
            type="number"
            step="any"
            placeholder="Longitude"
            value={formData.longitude}
            onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
            required
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
          <input
            type="text"
            placeholder="Address (optional)"
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
          />
          <div className="form-actions">
            <button type="submit" className="submit-btn">
              {editingStop ? 'Update Stop' : 'Create Stop'}
            </button>
            {editingStop && (
              <button type="button" onClick={cancelEdit} className="cancel-btn">
                Cancel
              </button>
            )}
          </div>
        </form>
      )}

      <div className="items-grid">
        {stops.map((stop) => (
          <div key={stop.stop_id} className="item-card">
            <div className="item-header">
              <h3>{stop.name}</h3>
              <div className="item-actions">
                <button onClick={() => handleEdit(stop)} className="edit-btn" title="Edit">
                  Edit
                </button>
                <button onClick={() => handleDelete(stop.stop_id)} className="delete-btn" title="Delete">
                  Delete
                </button>
              </div>
            </div>
            <p>Lat: {stop.latitude}, Lng: {stop.longitude}</p>
            {stop.description && <p className="description">{stop.description}</p>}
            {stop.address && <p className="address">{stop.address}</p>}
            {(stop.created_by || stop.updated_by) && (
              <div className="audit-info">
                {stop.created_by && <span>Created by: {stop.created_by}</span>}
                {stop.updated_by && <span>Updated by: {stop.updated_by}</span>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function PathsTab({ paths, stops, onRefresh }) {
  const [showForm, setShowForm] = useState(false)
  const [editingPath, setEditingPath] = useState(null)
  const [selectedStopIds, setSelectedStopIds] = useState([])
  const [formData, setFormData] = useState({
    path_name: '',
    description: '',
    total_distance_km: '',
    estimated_duration_minutes: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingPath) {
        await pathsAPI.update(editingPath.path_id, {
          ...formData,
          ordered_list_of_stop_ids: selectedStopIds,
          total_distance_km: parseFloat(formData.total_distance_km),
          estimated_duration_minutes: parseInt(formData.estimated_duration_minutes),
        })
      } else {
        await pathsAPI.create({
          ...formData,
          ordered_list_of_stop_ids: selectedStopIds,
          total_distance_km: parseFloat(formData.total_distance_km),
          estimated_duration_minutes: parseInt(formData.estimated_duration_minutes),
        })
      }
      setShowForm(false)
      setEditingPath(null)
      setSelectedStopIds([])
      setFormData({ path_name: '', description: '', total_distance_km: '', estimated_duration_minutes: '' })
      onRefresh()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || `Failed to ${editingPath ? 'update' : 'create'} path`
      alert(errorMsg)
      console.error(err)
    }
  }

  const handleEdit = (path) => {
    setEditingPath(path)
    setFormData({
      path_name: path.path_name || '',
      description: path.description || '',
      total_distance_km: path.total_distance_km || '',
      estimated_duration_minutes: path.estimated_duration_minutes || '',
    })
    setSelectedStopIds(path.ordered_list_of_stop_ids || [])
    setShowForm(true)
  }

  const handleAddStop = (stopId) => {
    if (!selectedStopIds.includes(stopId)) {
      setSelectedStopIds([...selectedStopIds, stopId])
    }
  }

  const handleRemoveStop = (index) => {
    setSelectedStopIds(selectedStopIds.filter((_, i) => i !== index))
  }

  const handleMoveStop = (index, direction) => {
    const newOrder = [...selectedStopIds]
    if (direction === 'up' && index > 0) {
      [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]]
    } else if (direction === 'down' && index < newOrder.length - 1) {
      [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]]
    }
    setSelectedStopIds(newOrder)
  }

  const getStopName = (stopId) => {
    const stop = stops.find(s => s.stop_id === stopId)
    return stop ? stop.name : `Stop ID: ${stopId}`
  }

  const handleDelete = async (pathId) => {
    if (window.confirm('Are you sure you want to delete this path?')) {
      try {
        await pathsAPI.delete(pathId, 1)
        onRefresh()
      } catch (err) {
        alert('Failed to delete path')
        console.error(err)
      }
    }
  }

  return (
    <div className="paths-tab">
      <div className="section-header">
        <h2>Paths</h2>
        <button onClick={() => setShowForm(!showForm)} className="add-btn">
          {showForm ? 'Cancel' : '+ Add Path'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="form">
          <h3>{editingPath ? 'Edit Path' : 'Create New Path'}</h3>
          <input
            type="text"
            placeholder="Path Name"
            value={formData.path_name}
            onChange={(e) => setFormData({ ...formData, path_name: e.target.value })}
            required
          />
          <input
            type="text"
            placeholder="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
          <input
            type="number"
            step="0.1"
            placeholder="Total Distance (km)"
            value={formData.total_distance_km}
            onChange={(e) => setFormData({ ...formData, total_distance_km: e.target.value })}
          />
          <input
            type="number"
            placeholder="Estimated Duration (minutes)"
            value={formData.estimated_duration_minutes}
            onChange={(e) => setFormData({ ...formData, estimated_duration_minutes: e.target.value })}
          />
          
          {/* Stops Selection */}
          <div className="stops-selection">
            <label>Select Stops (in order)</label>
            <select
              onChange={(e) => {
                if (e.target.value) {
                  handleAddStop(parseInt(e.target.value))
                  e.target.value = ''
                }
              }}
              className="stop-select"
            >
              <option value="">Add a stop...</option>
              {stops
                .filter(stop => !selectedStopIds.includes(stop.stop_id))
                .map(stop => (
                  <option key={stop.stop_id} value={stop.stop_id}>
                    {stop.name}
                  </option>
                ))}
            </select>
            
            {selectedStopIds.length > 0 && (
              <div className="selected-stops">
                <p className="selected-stops-label">Selected Stops (in order):</p>
                <div className="selected-stops-list">
                  {selectedStopIds.map((stopId, index) => (
                    <div key={`${stopId}-${index}`} className="selected-stop-item">
                      <span className="stop-order">{index + 1}.</span>
                      <span className="stop-name">{getStopName(stopId)}</span>
                      <div className="stop-item-actions">
                        <button
                          type="button"
                          onClick={() => handleMoveStop(index, 'up')}
                          disabled={index === 0}
                          className="move-btn"
                          title="Move up"
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          onClick={() => handleMoveStop(index, 'down')}
                          disabled={index === selectedStopIds.length - 1}
                          className="move-btn"
                          title="Move down"
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveStop(index)}
                          className="remove-stop-btn"
                          title="Remove"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="form-actions">
            <button type="submit" className="submit-btn">
              {editingPath ? 'Update Path' : 'Create Path'}
            </button>
            <button 
              type="button" 
              onClick={() => { 
                setShowForm(false)
                setEditingPath(null)
                setSelectedStopIds([])
              }} 
              className="cancel-btn"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="items-grid">
        {paths.map((path) => (
          <div key={path.path_id} className="item-card">
            <div className="item-header">
              <h3>{path.path_name}</h3>
              <div className="item-actions">
                <button onClick={() => handleEdit(path)} className="edit-btn" title="Edit">
                  Edit
                </button>
                <button onClick={() => handleDelete(path.path_id)} className="delete-btn" title="Delete">
                  Delete
                </button>
              </div>
            </div>
            <p>Stops: {path.ordered_list_of_stop_ids?.length || 0}</p>
            {path.description && <p className="description">{path.description}</p>}
            {path.total_distance_km && <p>Distance: {path.total_distance_km} km</p>}
            {(path.created_by || path.updated_by) && (
              <div className="audit-info">
                {path.created_by && <span>Created by: {path.created_by}</span>}
                {path.updated_by && <span>Updated by: {path.updated_by}</span>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function RoutesTab({ routes, paths, onRefresh }) {
  const [showForm, setShowForm] = useState(false)
  const [editingRoute, setEditingRoute] = useState(null)
  const [formData, setFormData] = useState({
    route_display_name: '',
    shift_time: '',
    direction: 'Forward',
    start_point: '',
    end_point: '',
    status: 'active',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingRoute) {
        await routesAPI.update(editingRoute.route_id, formData)
      } else {
        // For now, use first path - can be enhanced with dropdown
        const pathId = paths.length > 0 ? paths[0].path_id : null
        if (!pathId) {
          alert('Please create a path first')
          return
        }
        await routesAPI.create({
          ...formData,
          path_id: pathId,
        })
      }
      setShowForm(false)
      setEditingRoute(null)
      setFormData({ route_display_name: '', shift_time: '', direction: 'Forward', start_point: '', end_point: '', status: 'active' })
      onRefresh()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || `Failed to ${editingRoute ? 'update' : 'create'} route`
      alert(errorMsg)
      console.error(err)
    }
  }

  const handleEdit = (route) => {
    setEditingRoute(route)
    // Convert shift_time from HH:MM:SS to HH:MM for time input
    let shiftTime = route.shift_time || ''
    if (shiftTime && shiftTime.includes(':')) {
      const parts = shiftTime.split(':')
      shiftTime = `${parts[0]}:${parts[1]}` // Extract HH:MM
    }
    setFormData({
      route_display_name: route.route_display_name || '',
      shift_time: shiftTime,
      direction: route.direction || 'Forward',
      start_point: route.start_point || '',
      end_point: route.end_point || '',
      status: route.status || 'active',
    })
    setShowForm(true)
  }

  const handleDelete = async (routeId) => {
    if (window.confirm('Are you sure you want to delete this route?')) {
      try {
        await routesAPI.delete(routeId, 1)
        onRefresh()
      } catch (err) {
        alert('Failed to delete route')
        console.error(err)
      }
    }
  }

  return (
    <div className="routes-tab">
      <div className="section-header">
        <h2>Routes</h2>
        <button onClick={() => setShowForm(!showForm)} className="add-btn">
          {showForm ? 'Cancel' : '+ Add Route'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="form">
          <h3>{editingRoute ? 'Edit Route' : 'Create New Route'}</h3>
          <input
            type="text"
            placeholder="Route Display Name"
            value={formData.route_display_name}
            onChange={(e) => setFormData({ ...formData, route_display_name: e.target.value })}
            required
          />
          <input
            type="time"
            placeholder="Shift Time"
            value={formData.shift_time && formData.shift_time.includes(':') ? formData.shift_time.substring(0, 5) : (formData.shift_time || '')}
            onChange={(e) => setFormData({ ...formData, shift_time: e.target.value + ':00' })}
            required
          />
          <select
            value={formData.direction}
            onChange={(e) => setFormData({ ...formData, direction: e.target.value })}
          >
            <option value="Forward">Forward</option>
            <option value="Backward">Backward</option>
            <option value="Circular">Circular</option>
          </select>
          <input
            type="text"
            placeholder="Start Point"
            value={formData.start_point}
            onChange={(e) => setFormData({ ...formData, start_point: e.target.value })}
          />
          <input
            type="text"
            placeholder="End Point"
            value={formData.end_point}
            onChange={(e) => setFormData({ ...formData, end_point: e.target.value })}
          />
          <div className="form-actions">
            <button type="submit" className="submit-btn">
              {editingRoute ? 'Update Route' : 'Create Route'}
            </button>
            <button type="button" onClick={() => { setShowForm(false); setEditingRoute(null) }} className="cancel-btn">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="items-grid">
        {routes.map((route) => (
          <div key={route.route_id} className="item-card">
            <div className="item-header">
              <h3>{route.route_display_name}</h3>
              <div className="item-actions">
                <button onClick={() => handleEdit(route)} className="edit-btn" title="Edit">
                  Edit
                </button>
                <button onClick={() => handleDelete(route.route_id)} className="delete-btn" title="Delete">
                  Delete
                </button>
              </div>
            </div>
            <p>Time: {route.shift_time}</p>
            <p>Direction: {route.direction}</p>
            {(route.created_by || route.updated_by) && (
              <div className="audit-info">
                {route.created_by && <span>Created by: {route.created_by}</span>}
                {route.updated_by && <span>Updated by: {route.updated_by}</span>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default ManageRoute
