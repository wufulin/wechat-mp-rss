import { useState, useEffect, useMemo, useImperativeHandle, forwardRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'
import { searchMps } from '@/api/subscription'
import type { MpItem } from '@/api/subscription'

interface MpMultiSelectProps {
  value?: MpItem[]
  onChange?: (value: MpItem[]) => void
}

export interface MpMultiSelectRef {
  parseSelected: (data: MpItem[]) => void
}

const MpMultiSelect = forwardRef<MpMultiSelectRef, MpMultiSelectProps>(({ value = [], onChange }, ref) => {
  const [searchKeyword, setSearchKeyword] = useState('')
  const [loading, setLoading] = useState(false)
  const [mpList, setMpList] = useState<MpItem[]>([])
  const [selectedMps, setSelectedMps] = useState<MpItem[]>([])
  const [currentPage, setCurrentPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const pageSize = 10
  const getMpId = (mp: MpItem) => mp.id || mp.mp_id

  const formatCoverUrl = (url: string) => {
    if (!url) return ''
    if (/^https?:\/\/(mmbiz\.qpic\.cn|mmbiz\.qlogo\.cn|mmecoa\.qpic\.cn|wx\.qlogo\.cn|thirdwx\.qlogo\.cn)\//i.test(url)) {
      return '/static/res/logo/' + url
    }
    return url
  }

  const filteredMps = useMemo(() => {
    return mpList.filter((mp) =>
      !selectedMps.some((selected) => getMpId(selected) === getMpId(mp))
    )
  }, [mpList, selectedMps])

  const fetchMps = async (reset = true, page = currentPage) => {
    setLoading(true)
    try {
      let newPage = page
      let newMpList = mpList
      
      if (reset) {
        newPage = 0
        newMpList = []
      }
      
      const res = await searchMps(searchKeyword, {
        page: newPage,
        pageSize: pageSize
      })
      
      const mappedList: MpItem[] = (res.list || []).map((item) => ({
        id: item.mp_id || item.id,
        mp_id: item.mp_id || item.id,
        mp_name: item.mp_name,
        mp_cover: item.mp_cover || '',
        avatar: item.mp_cover || ''
      }))
      
      if (reset) {
        newMpList = mappedList
      } else {
        const newMps = mappedList.filter((newMp) =>
          !newMpList.some(existingMp => getMpId(existingMp) === getMpId(newMp))
        )
        newMpList = [...newMpList, ...newMps]
      }
      
      setMpList(newMpList)
      setCurrentPage(newPage)
      setHasMore((res.list || []).length === pageSize)
    } finally {
      setLoading(false)
    }
  }

  const loadMore = async () => {
    const nextPage = currentPage + 1
    setCurrentPage(nextPage)
    await fetchMps(false, nextPage)
  }

  const handleSearch = () => {
    fetchMps(true)
  }

  const toggleSelect = (mp: MpItem) => {
    const index = selectedMps.findIndex((m) => getMpId(m) === getMpId(mp))
    let newSelectedMps: MpItem[]
    if (index === -1) {
      newSelectedMps = [...selectedMps, mp]
    } else {
      newSelectedMps = selectedMps.filter(m => getMpId(m) !== getMpId(mp))
    }
    setSelectedMps(newSelectedMps)
    onChange?.(newSelectedMps)
  }

  const removeSelected = (mp: MpItem) => {
    const newSelectedMps = selectedMps.filter((m) => getMpId(m) !== getMpId(mp))
    setSelectedMps(newSelectedMps)
    onChange?.(newSelectedMps)
  }

  const clearAll = () => {
    setSelectedMps([])
    onChange?.([])
  }

  const selectAll = () => {
    const newSelectedMps = [...selectedMps]
    filteredMps.forEach((mp) => {
      if (!newSelectedMps.some((m) => getMpId(m) === getMpId(mp))) {
        newSelectedMps.push(mp)
      }
    })
    setSelectedMps(newSelectedMps)
    onChange?.(newSelectedMps)
  }

  const parseSelected = (data: MpItem[]) => {
    const parsed = data.map((item) => {
      const found = mpList.find((mp) => getMpId(mp) === getMpId(item))
      return found || {
        id: getMpId(item),
        mp_id: item.mp_id,
        mp_name: item.mp_name,
        mp_cover: item.mp_cover || item.avatar || '',
        avatar: item.avatar || item.mp_cover || ''
      }
    })
    setSelectedMps(parsed)
  }

  useImperativeHandle(ref, () => ({
    parseSelected
  }))

  useEffect(() => {
    fetchMps()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (value && value.length > 0) {
      parseSelected(value)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return (
    <Card>
      <CardHeader>
        <CardTitle>选择公众号</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="搜索公众号"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch()
              }
            }}
          />
          <Button onClick={handleSearch}>搜索</Button>
        </div>

        {loading && filteredMps.length === 0 ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <>
          {selectedMps.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium">已选公众号 ({selectedMps.length})</h4>
                  <Button variant="ghost" size="sm" onClick={clearAll}>清空</Button>
                </div>
                <div className="flex flex-wrap gap-2">
                {selectedMps.map((mp: MpItem) => (
                    <Badge
                      key={getMpId(mp)}
                      variant="secondary"
                      className="flex items-center gap-1 pr-1"
                    >
                      <Avatar className="h-5 w-5">
                        {(mp.mp_cover || mp.avatar) && (
                          <AvatarImage src={formatCoverUrl(mp.mp_cover || mp.avatar)} alt={mp.mp_name} />
                        )}
                        <AvatarFallback>{mp.mp_name?.[0] || 'M'}</AvatarFallback>
                      </Avatar>
                      <span>{mp.mp_name}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          removeSelected(mp)
                        }}
                        className="ml-1 hover:bg-destructive/20 rounded-full p-0.5"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">可选公众号</h4>
                <Button variant="ghost" size="sm" onClick={selectAll}>全选</Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {filteredMps.map((mp: MpItem) => (
                  <div
                    key={getMpId(mp)}
                    className="px-3 py-1.5 rounded-full cursor-pointer bg-muted hover:bg-muted/80 transition-colors flex items-center gap-2"
                    onClick={() => toggleSelect(mp)}
                  >
                    <Avatar className="h-6 w-6">
                      {(mp.mp_cover || mp.avatar) && (
                        <AvatarImage src={formatCoverUrl(mp.mp_cover || mp.avatar)} alt={mp.mp_name} />
                      )}
                      <AvatarFallback>{mp.mp_name?.[0] || 'M'}</AvatarFallback>
                    </Avatar>
                    <span className="text-sm">{mp.mp_name}</span>
                  </div>
                ))}
              </div>
          </div>
          
          {hasMore && (
              <div className="flex justify-center">
                <Button variant="ghost" onClick={loadMore} disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      加载中...
                    </>
                  ) : (
                    '加载更多'
                  )}
              </Button>
            </div>
          )}
          </>
        )}
      </CardContent>
    </Card>
  )
})

MpMultiSelect.displayName = 'MpMultiSelect'

export default MpMultiSelect
