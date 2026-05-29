interface ErrorBannerProps {
  message: string;
}

export default function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <section className="error-banner" role="alert">
      <strong>请求失败：</strong>
      <span>{message}</span>
    </section>
  );
}
