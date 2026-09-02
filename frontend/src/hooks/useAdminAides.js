import { useState, useEffect, useCallback } from 'react'
import adminService from '@/src/services/admin'

export default function useAdminAides() {
  const [aides, setAides] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await adminService.getAides()
      setAides(result)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetch() }, [fetch])

  const activateAide = useCallback(async (aideId) => {
    const updated = await adminService.activateAide(aideId)
    setAides((prev) => prev.map((a) => (a.aide_id === aideId ? updated : a)))
    return updated
  }, [])

  const deactivateAide = useCallback(async (aideId) => {
    const updated = await adminService.deactivateAide(aideId)
    setAides((prev) => prev.map((a) => (a.aide_id === aideId ? updated : a)))
    return updated
  }, [])

  const deleteAide = useCallback(async (aideId) => {
    await adminService.deleteAide(aideId)
    setAides((prev) => prev.filter((a) => a.aide_id !== aideId))
  }, [])

  const createAide = useCallback(async (payload) => {
    const created = await adminService.createAide(payload)
    setAides((prev) => [created, ...prev])
    return created
  }, [])

  return { aides, loading, error, refresh: fetch, activateAide, deactivateAide, deleteAide, createAide }
}
