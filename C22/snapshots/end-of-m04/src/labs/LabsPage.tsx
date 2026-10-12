// Labs: small pages that show one problem on purpose, for the lessons and the measurements.
import { JobLab } from './JobLab';
import { RaceLab } from './RaceLab';

const LABS = {
  race: { title: 'An old answer arrives last', Lab: RaceLab },
  job: { title: 'Follow a background job: polling or server-sent events', Lab: JobLab },
};

export function LabsPage({ lab }: { lab: string | null }) {
  const chosen = lab && lab in LABS ? LABS[lab as keyof typeof LABS] : null;
  if (chosen) return <chosen.Lab />;
  return (
    <section className="card" aria-labelledby="labs-heading">
      <h2 id="labs-heading">Labs</h2>
      <ul>
        {Object.entries(LABS).map(([id, l]) => (
          <li key={id}>
            <a href={`#/labs/${id}`}>{l.title}</a>
          </li>
        ))}
      </ul>
    </section>
  );
}
