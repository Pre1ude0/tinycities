<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import type { Page } from '$lib/types';

	let pages = $state<Page[] | null>([]);

	onMount(() => {
		fetch('/api/pages', {
			method: 'GET',
			headers: { accept: 'application/json' },
			credentials: 'include'
		})
			.then(async (res) => {
				if (!res.ok) {
					const text = await res.text();
					throw new Error(text || `Request failed (${res.status})`);
				}

				const data = await res.json();
				if (!Array.isArray(data.pages)) {
					throw new Error('Invalid response format');
				}

				pages = data.pages as Page[];
				pages = pages.sort((a, b) => (b.role ?? -Infinity) - (a.role ?? -Infinity));
			})
			.catch((e) => {
				console.error(e instanceof Error ? e.message : String(e));
			});
	});
</script>

{#if pages}
	<div class="flex flex-col gap-5">
		{#if pages.filter((page) => page.role === 2).length > 0}
			<div class="flex flex-col gap-2">
				<h2 class="text-lg font-bold">My pages</h2>
				{#each pages.filter((page) => page.role === 2) as page}
					<a href={`?edit=${page.id}`} class="ml-2 font-semibold"
						>{page.name || page.external_url}</a
					>
				{/each}
			</div>
		{/if}
		{#if pages.filter((page) => page.role === 1).length > 0}
			<h2 class="text-lg font-bold text-yellow-500">Contributors</h2>
			{#each pages.filter((page) => page.role === 1) as page}
				<div class="flex flex-row items-end gap-2">
					<h3 class="font-semibold">{page.name || page.external_url}</h3>
					<span class="text-yellow-500">Contributor</span>
				</div>
			{/each}
		{/if}
		{#if pages.filter((page) => page.role === 0).length > 0}
			<h2 class="text-lg font-bold text-gray-500">Viewers</h2>
			{#each pages.filter((page) => page.role === 0) as page}
				<div class="flex flex-row items-end gap-2">
					<h3 class="font-semibold">{page.name || page.external_url}</h3>
					<span class="text-gray-500">Viewer</span>
				</div>
			{/each}
		{/if}
	</div>
{/if}
