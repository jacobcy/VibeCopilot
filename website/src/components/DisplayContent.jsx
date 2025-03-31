import React, { useState, useEffect } from 'react';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {useColorMode} from '@docusaurus/theme-common';
import CodeBlock from '@theme/CodeBlock';
import styles from './DisplayContent.module.css';

/**
 * 用于显示嵌入内容的组件
 */
export function DisplayContent({path, children}) {
  const [content, setContent] = useState(null);
  const [error, setError] = useState(null);
  const {colorMode} = useColorMode();
  const {siteConfig} = useDocusaurusContext();
  const baseUrl = siteConfig.baseUrl;

  useEffect(() => {
    // 构建内容URL
    const contentUrl = useBaseUrl(`/docs/${path}.md`);

    // 获取内容
    fetch(contentUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`无法加载内容: ${response.status} ${response.statusText}`);
        }
        return response.text();
      })
      .then(text => {
        setContent(text);
        setError(null);
      })
      .catch(err => {
        console.error('加载内容时出错:', err);
        setError(`无法加载内容: ${err.message}`);
        setContent(null);
      });
  }, [path, baseUrl]);

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <p>❌ {error}</p>
        <p>路径: {path}</p>
      </div>
    );
  }

  if (!content) {
    return <div className={styles.loading}>加载内容中...</div>;
  }

  // 显示嵌入内容
  return (
    <div className={`${styles.embedContainer} ${styles[colorMode]}`}>
      <div className={styles.embedHeader}>
        {children || '嵌入内容'}
        <span className={styles.embedPath}>{path}</span>
      </div>
      <div className={styles.embedContent}>
        <CodeBlock language="markdown">
          {content}
        </CodeBlock>
      </div>
    </div>
  );
}

export default DisplayContent;
