import React, { useEffect, useState } from 'react';
import { Button, Card, Checkbox, Input, message, Select, Space, Table, Upload } from 'antd';
import { UploadOutlined, DownloadOutlined, SearchOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import {
  FileInfo,
  FilterItem,
  useCurrentFile,
  useRecentFiles,
  fileApi,
  exportApi,
  queryApi,
  taskApi,
  ParsedTask,
} from './api';

const SAFE_FIELDS = [
  '用户名', '姓名', '证件姓名', '所属部门', '合同主体',
  '劳动合同/协议开始日', '劳动合同/协议结束日期', '工时性质', '社保缴纳地', '工作地点名称', 'HRBP姓名', 'HRBP Head姓名',
];

function App() {
  const { current, loading, refresh } = useCurrentFile();
  const { files, refresh: refreshRecent } = useRecentFiles();
  
  // LLM配置状态
  const [llmConfig, setLlmConfig] = useState({ provider: 'deepseek', baseUrl: 'https://api.deepseek.com', model: 'deepseek-chat', apiKey: '', configured: false });
  const [showLlmConfig, setShowLlmConfig] = useState(false);
  
  // 获取LLM配置
  useEffect(() => {
    fetch('/api/llm/config')
      .then(res => res.json())
      .then(data => setLlmConfig(prev => ({ ...prev, ...data })))
      .catch(() => {});
  }, []);

  // 从后端获取的列中，过滤掉敏感字段（用于导出字段选择）
  const availableColumns = current?.columns?.filter(col => 
    !['身份证号', '证件号码', '银行卡号', '开户行', '邮箱', '薪资', '手机号', '联系电话', 
      '家庭住址', '现住址', '紧急联系人', '紧急联系人电话', '个人邮箱', '社保账号', '公积金账号'].includes(col)
  ) || [];

  const [exportFilters, setExportFilters] = useState<Record<string, string>>({});
  const [exportColumns, setExportColumns] = useState<string[]>([]); // 空表示导出所有可用列
  const [exportResult, setExportResult] = useState<{ count: number; columns: string[]; rows: Record<string, unknown>[] } | null>(null);
  const [exportDownloadUrl, setExportDownloadUrl] = useState<string | null>(null);

  const [quickQuery, setQuickQuery] = useState('');
  const [quickResult, setQuickResult] = useState<any>(null);

  const [chatMessages, setChatMessages] = useState<{ role: string; content: string; parsed?: ParsedTask }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatPreviewData, setChatPreviewData] = useState<{ count: number; columns: string[]; rows: Record<string, unknown>[] } | null>(null);

  const handleUpload = async (file: File) => {
    try {
      await fileApi.upload(file);
      message.success('文件上传成功');
      refresh();
      refreshRecent();
    } catch (e) {
      message.error('上传失败: ' + (e as Error).message);
    }
    return false;
  };

  const handleSelectFile = async (fileId: string) => {
    try {
      await fileApi.select(fileId);
      refresh();
      message.success('已切换文件');
    } catch (e) {
      message.error('切换失败');
    }
  };

  const handleExportPreview = async () => {
    if (!current) {
      message.error('请先上传或选择文件');
      return;
    }
    const filters: FilterItem[] = Object.entries(exportFilters)
      .filter(([, value]) => value.trim())
      .map(([field, value]) => {
        const trimmed = value.trim();
        let operator: string = 'equals';
        let parsedValue = trimmed;
        
        // 解析操作符前缀
        if (trimmed.startsWith('>=')) {
          operator = 'gte';
          parsedValue = trimmed.slice(2).trim();
        } else if (trimmed.startsWith('<=')) {
          operator = 'lte';
          parsedValue = trimmed.slice(2).trim();
        } else if (trimmed.startsWith('>')) {
          operator = 'gt';
          parsedValue = trimmed.slice(1).trim();
        } else if (trimmed.startsWith('<')) {
          operator = 'lt';
          parsedValue = trimmed.slice(1).trim();
        } else if (trimmed.startsWith('=')) {
          operator = 'equals';
          parsedValue = trimmed.slice(1).trim();
        } else if (trimmed.startsWith('包含')) {
          operator = 'contains';
          parsedValue = trimmed.slice(2).trim();
        }
        
        return { field, operator, value: parsedValue };
      });
    try {
      const result = await exportApi.preview({ fileId: current.id, filters, columns: exportColumns });
      setExportResult(result);
      setExportDownloadUrl(null);
      message.success(`找到 ${result.count} 条记录`);
    } catch (e) {
      message.error('预览失败: ' + (e as Error).message);
    }
  };

  const handleExportExcel = async () => {
    if (!current) {
      message.error('请先上传或选择文件');
      return;
    }
    const filters: FilterItem[] = Object.entries(exportFilters)
      .filter(([, value]) => value.trim())
      .map(([field, value]) => {
        const trimmed = value.trim();
        let operator: string = 'equals';
        let parsedValue = trimmed;
        
        if (trimmed.startsWith('>=')) {
          operator = 'gte';
          parsedValue = trimmed.slice(2).trim();
        } else if (trimmed.startsWith('<=')) {
          operator = 'lte';
          parsedValue = trimmed.slice(2).trim();
        } else if (trimmed.startsWith('>')) {
          operator = 'gt';
          parsedValue = trimmed.slice(1).trim();
        } else if (trimmed.startsWith('<')) {
          operator = 'lt';
          parsedValue = trimmed.slice(1).trim();
        } else if (trimmed.startsWith('=')) {
          operator = 'equals';
          parsedValue = trimmed.slice(1).trim();
        } else if (trimmed.startsWith('包含')) {
          operator = 'contains';
          parsedValue = trimmed.slice(2).trim();
        }
        
        return { field, operator, value: parsedValue };
      });
    try {
      const result = await exportApi.excel({ fileId: current.id, filters, columns: exportColumns });
      setExportDownloadUrl(result.downloadUrl);
      message.success('导出成功');
    } catch (e) {
      message.error('导出失败: ' + (e as Error).message);
    }
  };

  const handleQuickQuery = async () => {
    if (!current) {
      message.error('请先上传或选择文件');
      return;
    }
    if (!quickQuery.trim()) return;
    try {
      const result = await queryApi.quick({ fileId: current.id, query: quickQuery });
      setQuickResult(result);
    } catch (e) {
      message.error('查询失败: ' + (e as Error).message);
    }
  };

  const handleChatSend = async () => {
    if (!current) {
      message.error('请先上传或选择文件');
      return;
    }
    if (!chatInput.trim()) return;
    
    // 检查是否配置了LLM
    if (!llmConfig.configured || !llmConfig.apiKey) {
      setShowLlmConfig(true);
      message.warning('请先配置大模型API Key');
      return;
    }

    const userMsg = chatInput;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);
    
    // 清空之前的预览数据
    setChatPreviewData(null);
    setExportDownloadUrl(null);

    try {
      // 调用后端LLM接口
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          fileId: current.id,
          availableColumns: current.columns,
          // 只发送role和content，不发送parsed等额外字段
          history: chatMessages.slice(-6).map(m => ({ role: m.role, content: m.content }))
        }),
      });
      
      if (!response.ok) {
        throw new Error('请求失败');
      }
      
      const result = await response.json();
      
      if (result.type === 'query' || result.type === 'export') {
        // 查询或导出请求 - 显示预览
        setChatMessages(prev => [...prev, { 
          role: 'assistant', 
          content: result.explanation || `✅ 已找到 ${result.count} 条记录，请查看下方预览表格。满意后可点击下载按钮。`
        }]);
        
        // 显示预览表格
        setChatPreviewData({
          count: result.count || 0,
          columns: result.columns || [],
          rows: result.rows || []
        });
        
        // 后端已生成下载链接，暂存
        if (result.downloadUrl) {
          setExportDownloadUrl(result.downloadUrl);
        }
      } else {
        // 普通对话
        setChatMessages(prev => [...prev, { 
          role: 'assistant', 
          content: result.message || result.explanation || '收到'
        }]);
      }
      
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: `错误：${(e as Error).message}` }]);
    } finally {
      setChatLoading(false);
    }
  };
  
  // 保存LLM配置
  const handleSaveLlmConfig = async () => {
    try {
      const response = await fetch('/api/llm/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(llmConfig)
      });
      if (response.ok) {
        message.success('配置保存成功');
        setLlmConfig(prev => ({ ...prev, configured: true }));
        setShowLlmConfig(false);
      }
    } catch (e) {
      message.error('保存失败');
    }
  };

  return (
    <div className="app-container">
      {/* Top Bar */}
      <div className="top-bar">
        <span className="file-label">数据源：</span>
        {loading ? (
          <span>加载中...</span>
        ) : current ? (
          <span className="file-name">{current.fileName}</span>
        ) : (
          <span className="file-name" style={{ color: '#999' }}>未选择文件</span>
        )}
        <Upload accept=".xlsx,.xls" beforeUpload={handleUpload} showUploadList={false}>
          <Button icon={<UploadOutlined />} size="small">上传</Button>
        </Upload>
        {files.length > 0 && (
          <Select
            size="small"
            style={{ width: 200 }}
            placeholder="选择历史文件"
            value={current?.id}
            onChange={handleSelectFile}
            options={files.map(f => ({ value: f.id, label: f.fileName }))}
          />
        )}
        <Button icon={<ReloadOutlined />} size="small" onClick={() => { refresh(); refreshRecent(); }}>刷新</Button>
      </div>

      <div className="main-content">
        {/* Section 1: Quick Query */}
        <Card className="section-card" title={<span className="section-title">🔍 信息查询</span>}>
          <div className="query-input-row">
            <Input
              placeholder="输入：张三 hrbp / 张三 合同主体"
              value={quickQuery}
              onChange={e => setQuickQuery(e.target.value)}
              onPressEnter={handleQuickQuery}
            />
            <Button type="primary" icon={<SearchOutlined />} onClick={handleQuickQuery}>查询</Button>
          </div>
          <div className="quick-hints">
            <span style={{ fontSize: 13, color: '#999', lineHeight: '24px' }}>快捷指令：</span>
            {['hrbp', '合同主体', '合同结束日期', '社保地', '工作地'].map(hint => (
              <span
                key={hint}
                className="ant-tag"
                style={{ cursor: 'pointer', margin: '4px' }}
                onClick={() => setQuickQuery(hint + ' ')}
              >
                {hint}
              </span>
            ))}
          </div>
          {quickResult && (
            <div className="result-area">
              {quickResult.matchType === 'single' && (
                <div>
                  <div style={{ marginBottom: 8, color: '#52c41a' }}>✅ 找到 1 条记录</div>
                  <div className="table-container">
                    <Table 
                      columns={Object.keys(quickResult.record || {}).map(k => ({ 
                        title: k, 
                        dataIndex: k, 
                        key: k, 
                        width: 200,
                        ellipsis: true
                      }))} 
                      dataSource={[quickResult.record]} 
                      rowKey={() => '0'} 
                      pagination={false} 
                      size="small"
                      scroll={{ x: true }}
                    />
                  </div>
                </div>
              )}
              {quickResult.matchType === 'multiple' && (
                <div>
                  <div style={{ marginBottom: 8 }}>✅ 找到 {quickResult.count} 条匹配记录</div>
                  <div className="table-container">
                    <Table 
                      columns={Object.keys(quickResult.rows?.[0] || {}).map(k => ({ 
                        title: k, 
                        dataIndex: k, 
                        key: k, 
                        width: 200,
                        ellipsis: true
                      }))} 
                      dataSource={quickResult.rows} 
                      rowKey={(record, index) => index ?? 0} 
                      pagination={{ pageSize: 10 }} 
                      size="small"
                      scroll={{ x: true }}
                    />
                  </div>
                </div>
              )}
              {quickResult.matchType === 'none' && (
                <div className="result-card" style={{ color: '#999' }}>{quickResult.message}</div>
              )}
            </div>
          )}
        </Card>

        {/* Section 2: Export */}
        <Card className="section-card" title={<span className="section-title">📤 字段导出 Excel</span>}>
          {/* 固定的常用字段筛选区 */}
          <div className="filter-grid">
            {SAFE_FIELDS.map(field => (
              <div className="filter-item" key={field}>
                <label>{field}</label>
                <Input
                  placeholder="如：=值 / 包含 / <日期"
                  value={exportFilters[field] || ''}
                  onChange={e => setExportFilters({ ...exportFilters, [field]: e.target.value })}
                />
              </div>
            ))}
          </div>
          {/* 动态导出字段选择区 */}
          <div style={{ marginTop: 12 }}>
            <label style={{ fontSize: 13, color: '#555', marginRight: 8 }}>导出字段（可多选，默认全部）：</label>
            <div style={{ maxHeight: 120, overflowY: 'auto', border: '1px solid #d9d9d9', borderRadius: 6, padding: 8 }}>
              <Checkbox.Group
                value={exportColumns}
                onChange={vals => setExportColumns(vals as string[])}
                options={availableColumns.map(col => ({ label: col, value: col }))}
              />
            </div>
            <div style={{ marginTop: 8 }}>
              <Button size="small" onClick={() => setExportColumns(availableColumns)}>全选</Button>
              <Button size="small" style={{ marginLeft: 8 }} onClick={() => setExportColumns([])}>清空</Button>
            </div>
          </div>
          <div className="action-bar">
            <Button type="primary" icon={<SearchOutlined />} onClick={handleExportPreview}>预览结果</Button>
            <Button icon={<DownloadOutlined />} onClick={handleExportExcel}>导出 Excel</Button>
            <Button onClick={() => { setExportFilters({}); setExportColumns([]); setExportResult(null); setExportDownloadUrl(null); }}>清空</Button>
          </div>
          {exportResult && (
            <div className="result-area">
              <div style={{ marginBottom: 8, color: '#666' }}>共 {exportResult.count} 条记录</div>
              <Table 
                columns={exportResult.columns.map(col => ({ title: col, dataIndex: col, key: col, ellipsis: true, width: 150 }))} 
                dataSource={exportResult.rows} 
                rowKey={(record, index) => index ?? 0} 
                pagination={{ pageSize: 10 }} 
                size="small" 
                scroll={{ x: 'max-content' }}
              />
              {exportDownloadUrl && (
                <div className="download-link">
                  <a href={exportDownloadUrl} download>
                    <Button type="link" icon={<DownloadOutlined />}>下载 Excel 文件</Button>
                  </a>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Section 3: Natural Language Task */}
        <Card className="section-card" title={
          <span className="section-title">
            💬 自然语言任务
            <Button 
              size="small" 
              type="link" 
              icon={<SettingOutlined />} 
              onClick={() => setShowLlmConfig(true)}
              style={{ float: 'right', marginTop: -4 }}
            >
              配置API
            </Button>
          </span>
        }>
          <div style={{ padding: 12, background: llmConfig.configured ? '#f6ffed' : '#fff7e6', borderRadius: 8, marginBottom: 12, fontSize: 13 }}>
            <b>{llmConfig.configured ? '✅ AI助手已就绪' : '⚠️ 请先配置大模型API'}</b>
            <br/>• 支持自然语言对话和智能查询
            <br/>• 推荐使用 DeepSeek（免费额度）
          </div>
          
          <div className="chat-area">
            <div className="chat-messages" style={{ height: 200, overflowY: 'auto' }}>
              {chatMessages.map((msg, i) => (
                <div key={i} className={`chat-message ${msg.role}`}>
                  {msg.content}
                  {msg.parsed && (
                    <div style={{ marginTop: 4, fontSize: 12, opacity: 0.8 }}>
                      条件：{msg.parsed.filters.map(f => `${f.field} ${f.operator} ${f.value}`).join(' 且 ')}
                    </div>
                  )}
                </div>
              ))}
              {chatLoading && <div className="chat-message assistant">思考中...</div>}
            </div>
            <div className="chat-input-row">
              <Input
                placeholder="问我任何问题，例如：找出电商部门的员工"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onPressEnter={handleChatSend}
                disabled={chatLoading}
              />
              <Button type="primary" onClick={handleChatSend} loading={chatLoading}>发送</Button>
            </div>
            
            {/* 预览结果表格 */}
            {chatPreviewData && chatPreviewData.rows && chatPreviewData.rows.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ marginBottom: 8, fontWeight: 'bold', color: '#1890ff' }}>
                  📊 预览结果（共 {chatPreviewData.count} 条，显示前 {chatPreviewData.rows.length} 条）
                </div>
                <div className="chat-preview-container">
                  <Table 
                    columns={chatPreviewData.columns.map(k => ({ 
                      title: k, 
                      dataIndex: k, 
                      key: k, 
                      width: 200,
                      ellipsis: true
                    }))} 
                    dataSource={chatPreviewData.rows} 
                    rowKey={(record, index) => index ?? 0} 
                    pagination={false}
                    size="small"
                    scroll={{ x: true, y: 350 }}
                  />
                </div>
                
                {/* 下载按钮 */}
                {exportDownloadUrl && (
                  <div style={{ marginTop: 16, textAlign: 'center' }}>
                    <a href={exportDownloadUrl} download>
                      <Button type="primary" icon={<DownloadOutlined />} size="large">
                        💾 下载Excel文件（{chatPreviewData?.count || 0} 条记录）
                      </Button>
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      </div>
      
      {/* LLM配置弹窗 */}
      {showLlmConfig && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#fff', padding: 24, borderRadius: 8, width: 450 }}>
            <h3 style={{ marginTop: 0 }}>🤖 大模型配置</h3>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 4 }}>服务商</label>
              <Select value={llmConfig.provider} onChange={v => setLlmConfig({ ...llmConfig, provider: v })} style={{ width: '100%' }}>
                <Select.Option value="deepseek">DeepSeek（推荐，有免费额度）</Select.Option>
                <Select.Option value="openai">OpenAI</Select.Option>
                <Select.Option value="qwen">通义千问</Select.Option>
                <Select.Option value="custom">自定义</Select.Option>
              </Select>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 4 }}>API Base URL</label>
              <Input 
                value={llmConfig.baseUrl} 
                onChange={e => setLlmConfig({ ...llmConfig, baseUrl: e.target.value })}
                placeholder="https://api.deepseek.com"
              />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 4 }}>模型名称</label>
              <Input 
                value={llmConfig.model} 
                onChange={e => setLlmConfig({ ...llmConfig, model: e.target.value })}
                placeholder="deepseek-chat"
              />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 4 }}>API Key</label>
              <Input.Password 
                value={llmConfig.apiKey} 
                onChange={e => setLlmConfig({ ...llmConfig, apiKey: e.target.value })}
                placeholder="sk-..."
              />
              <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                DeepSeek获取：platform.deepseek.com
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <Button onClick={() => setShowLlmConfig(false)} style={{ marginRight: 8 }}>取消</Button>
              <Button type="primary" onClick={handleSaveLlmConfig}>保存配置</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
