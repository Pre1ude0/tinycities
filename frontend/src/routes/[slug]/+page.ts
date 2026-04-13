import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = ({ params }) => {
	const slug = params.slug;
	if (slug === 'login' || slug === 'register') {
		return { slug };
	}
	error(404, { message: 'Not found' });
};
