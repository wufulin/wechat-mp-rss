import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { PageHeader } from '@/components/extensions/page-header'
import { useToast } from '@/hooks/use-toast'
import { getMessageTask, createMessageTask, updateMessageTask } from '@/api/messageTask'
import type { MessageTaskCreate } from '@/types/messageTask'
import CronExpressionPicker from '@/components/CronExpressionPicker'
import MpMultiSelect from '@/components/MpMultiSelect'
import ACodeEditor from '@/components/ACodeEditor'

const formSchema = z.object({
  name: z.string().min(2, '任务名称长度应在2-30个字符之间').max(30, '任务名称长度应在2-30个字符之间'),
  message_type: z.number(),
  message_template: z.string().optional(),
  web_hook_url: z.string().optional(),
  mps_id: z.array(z.any()).optional(),
  status: z.number(),
  cron_exp: z.string().min(1, '请输入cron表达式'),
})

const MessageTaskForm: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [showCronPicker, setShowCronPicker] = useState(false)
  const [showMpSelector, setShowMpSelector] = useState(false)
  const { toast } = useToast()
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      message_type: 0,
      message_template: '',
      web_hook_url: '',
      mps_id: [],
      status: 1,
      cron_exp: '',
    },
  })

  useEffect(() => {
    if (id) {
      setIsEditMode(true)
      fetchTaskDetail(id)
    }
  }, [id])

  const fetchTaskDetail = async (taskId: string) => {
    setLoading(true)
    try {
      const res = await getMessageTask(taskId) as any
      form.reset({
        name: res.name,
        message_type: res.message_type,
        message_template: res.message_template,
        web_hook_url: res.web_hook_url,
        mps_id: JSON.parse(res.mps_id || '[]'),
        status: res.status,
        cron_exp: res.cron_exp
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (values: z.infer<typeof formSchema>) => {
    setLoading(true)

    try {
      const submitData = {
        ...values,
        mps_id: JSON.stringify(values.mps_id || [])
      } as MessageTaskCreate

      if (isEditMode && id) {
        await updateMessageTask(id, submitData)
        toast({
          title: '成功',
          description: '更新任务成功，点击应用按钮后任务才会生效',
        })
      } else {
        await createMessageTask(submitData)
        toast({
          title: '成功',
          description: '创建任务成功，点击应用按钮后任务才会生效',
        })
      }
      setTimeout(() => {
        navigate('/message-tasks')
      }, 1500)
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: '错误',
        description: error?.errors?.join('\n') || '表单验证失败，请检查输入内容',
      })
    } finally {
      setLoading(false)
    }
  }

  const cronExp = form.watch('cron_exp')
  const messageType = form.watch('message_type')
  const mpsId = form.watch('mps_id') || []

  if (loading && !form.formState.isDirty) {
    return (
      <div className="p-6 max-w-[1200px] mx-auto">
        <Skeleton className="h-8 w-48 mb-6" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <PageHeader
        title={isEditMode ? '编辑消息任务' : '添加消息任务'}
        subTitle={isEditMode ? '修改消息任务的配置信息' : '创建新的消息任务，定时发送订阅内容'}
        onBack={() => navigate(-1)}
      />

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{isEditMode ? '编辑消息任务' : '添加消息任务'}</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>任务名称 <span className="text-destructive">*</span></FormLabel>
                    <FormControl>
                      <Input placeholder="请输入任务名称" {...field} className="max-w-[600px]" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="message_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>类型</FormLabel>
                    <FormControl>
                      <Select
                        value={field.value?.toString()}
                        onValueChange={(value) => field.onChange(parseInt(value))}
                      >
                        <SelectTrigger className="w-[200px]">
                          <SelectValue placeholder="选择消息类型" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">Message</SelectItem>
                          <SelectItem value="1">WebHook</SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

          <FormField
            control={form.control}
            name="message_template"
            render={({ field }) => (
              <FormItem>
                <FormLabel>消息模板</FormLabel>
                <FormControl>
                  <div>
                    <ACodeEditor
                      value={field.value || ''}
                      onChange={(value) => field.onChange(value)}
                      placeholder="请输入消息模板内容"
                      language="custom"
                    />
                    {messageType === 0 ? (
                      <div className="mt-2 flex gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            const mpsId = form.watch('mps_id') || []
                            const isMultiple = mpsId.length > 1
                            
                            if (isMultiple) {
                              // 多个公众号：使用聚合模板
                              form.setValue('message_template', '{{ today }} 每日科技聚合资讯\n\n{% for item in feeds_with_articles %}\n## {{ item.feed.mp_name }}\n\n{% for article in item.articles %}\n- [**{{ article.title }}**]({{ article.url }}){% if article.tag_names %} 🏷️ {{= \', \'.join(article.tag_names) if isinstance(article.tag_names, list) else str(article.tag_names) }}{% endif %}\n{% endfor %}\n\n{% endfor %}\n\n---\n📊 共 {{ total_articles }} 篇文章，来自 {{ feeds_count }} 个公众号')
                            } else {
                              // 单个公众号：使用单个公众号模板
                              form.setValue('message_template', '### {{feed.mp_name}} 订阅消息：\n{% if articles %}\n{% for article in articles %}\n- [**{{ article.title }}**]({{article.url}}){% if article.tag_names %} 🏷️ {{= \', \'.join(article.tag_names) if isinstance(article.tag_names, list) else str(article.tag_names) }}{% endif %}\n{% endfor %}\n{% else %}\n- 暂无文章\n{% endif %}')
                            }
                          }}
                        >
                          使用示例消息模板
                        </Button>
                      </div>
                    ) : (
                      <Button
                        type="button"
                        variant="outline"
                        className="mt-2"
                        onClick={() => form.setValue('message_template', '{\n    \'articles\': [\n    {% for article in articles %}\n    {{article}}\n    {% if not loop.last %},{% endif %}\n    {% endfor %}\n    ]\n}')}
                      >
                        使用示例WebHook模板
                      </Button>
                    )}
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

              <FormField
                control={form.control}
                name="web_hook_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>WebHook地址</FormLabel>
                    <FormControl>
                      <div className="space-y-2 max-w-[700px]">
                        <Input placeholder="请输入WebHook地址" {...field} />
                        <a
                          href="https://open.dingtalk.com/document/orgapp/obtain-the-webhook-address-of-a-custom-robot"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline"
                        >
                          如何获取WebHook
                        </a>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

          <FormField
            control={form.control}
            name="cron_exp"
            render={() => (
              <FormItem>
                <FormLabel>cron表达式 <span className="text-destructive">*</span></FormLabel>
                <FormControl>
                  <div className="flex gap-2">
                    <Input
                      value={cronExp || ''}
                      placeholder="请输入cron表达式"
                      readOnly
                      className="flex-1 max-w-[500px]"
                    />
                    <Button type="button" onClick={() => setShowCronPicker(true)}>选择</Button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="mps_id"
            render={() => (
              <FormItem>
                <FormLabel>公众号</FormLabel>
                <FormControl>
                  <div className="flex gap-2">
                    <Input
                      value={mpsId.map((mp: any) => mp.id?.toString() || '').join(',')}
                      placeholder="请选择公众号，留空则对所有公众号生效"
                      readOnly
                      className="flex-1 max-w-[500px]"
                    />
                    <Button type="button" onClick={() => setShowMpSelector(true)}>选择</Button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>状态</FormLabel>
                    <FormControl>
                      <Select
                        value={field.value?.toString()}
                        onValueChange={(value) => field.onChange(parseInt(value))}
                      >
                        <SelectTrigger className="w-[200px]">
                          <SelectValue placeholder="选择状态" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">启用</SelectItem>
                          <SelectItem value="0">禁用</SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex gap-2 pt-4">
                <Button type="submit" disabled={loading}>
                  {loading ? '提交中...' : '提交'}
                </Button>
                <Button type="button" variant="outline" onClick={() => navigate(-1)}>取消</Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Dialog open={showCronPicker} onOpenChange={setShowCronPicker}>
        <DialogContent className="max-w-[800px] max-h-[90vh] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle>选择cron表达式</DialogTitle>
            <DialogDescription>选择或自定义任务执行的 cron 表达式</DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto min-h-0 px-1">
            <CronExpressionPicker
              value={cronExp || ''}
              onChange={(value) => form.setValue('cron_exp', value)}
            />
          </div>
          <DialogFooter className="flex-shrink-0">
            <Button onClick={() => setShowCronPicker(false)}>确定</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showMpSelector} onOpenChange={setShowMpSelector}>
        <DialogContent className="max-w-[800px]">
          <DialogHeader>
            <DialogTitle>选择公众号</DialogTitle>
            <DialogDescription>选择要发送消息的公众号</DialogDescription>
          </DialogHeader>
          <MpMultiSelect
            value={mpsId}
            onChange={(value) => form.setValue('mps_id', value)}
          />
          <DialogFooter>
            <Button onClick={() => setShowMpSelector(false)}>确定</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default MessageTaskForm
