export default function LoadingState() {
  return (
    <section className="card loading-wrap" aria-live="polite">
      <div className="spinner" />
      <p>正在分析 PR，请稍候...</p>
    </section>
  );
}
