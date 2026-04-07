import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="text-center py-16">
        <h1 className="text-5xl font-bold tracking-tight text-gray-900">
          Mishmash
        </h1>
        <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
          The open platform for collaborative data analysis. Upload datasets,
          run reproducible analyses, and share your findings with the world.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            href="/datasets"
            className="rounded-lg bg-brand-600 px-6 py-3 text-white font-medium hover:bg-brand-700 transition"
          >
            Browse Datasets
          </Link>
          <Link
            href="/analyses"
            className="rounded-lg border border-gray-300 px-6 py-3 font-medium hover:bg-gray-100 transition"
          >
            Explore Analyses
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <FeatureCard
          title="Upload & Version"
          description="Upload CSV, JSON, or Parquet datasets. Every change is versioned so you can always go back."
        />
        <FeatureCard
          title="Analyze & Reproduce"
          description="Write Python or R scripts that run against datasets in sandboxed environments. Every result is reproducible."
        />
        <FeatureCard
          title="Share & Discuss"
          description="Publish findings linked to source data. Comment, reference datasets, and build on each other's work."
        />
      </section>

      {/* How it works */}
      <section className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
        <h2 className="text-2xl font-bold text-center mb-8">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Step number={1} title="Upload" description="Drop your dataset files — CSV, JSON, or Parquet" />
          <Step number={2} title="Analyze" description="Write code that processes and transforms the data" />
          <Step number={3} title="Connect" description="Reference and combine datasets to discover correlations" />
          <Step number={4} title="Publish" description="Share your findings with full provenance and reproducibility" />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-gray-600">{description}</p>
    </div>
  );
}

function Step({ number, title, description }: { number: number; title: string; description: string }) {
  return (
    <div className="text-center">
      <div className="mx-auto w-10 h-10 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-lg">
        {number}
      </div>
      <h3 className="mt-3 font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-gray-600">{description}</p>
    </div>
  );
}
