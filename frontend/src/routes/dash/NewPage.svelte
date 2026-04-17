<script lang="ts">
	import { page } from '$app/state';
	import type { Page } from '$lib/types';
	let { pages = $bindable() } = $props();

	let mode = $state<'claim' | 'add'>('claim');

	let subdomain = $state<string>('');
	let externalDomain = $state<string>('');
	let error = $state<string | null>(null);

	async function addPage(page_name: string | null, external_url: string | null) {
		error = null;

		let req = await fetch('/api/pages', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			credentials: 'include',
			body: JSON.stringify({ page_name, is_private: false, external_url })
		});

		if (!req.ok) {
			const data = await req.json();
			error = data.detail || `Request failed (${req.status})`;
			return;
		}

		const listReq = await fetch('/api/pages', {
			method: 'GET',
			headers: { accept: 'application/json' },
			credentials: 'include'
		});

		if (!listReq.ok) {
			const text = await listReq.text();
			error = text || `Request failed (${listReq.status})`;
			return;
		}

		const data = await listReq.json();
		if (!Array.isArray(data.pages)) {
			error = 'Invalid response format';
			return;
		}

		pages = data.pages as Page[];
	}
</script>

<div>
	<div class="flex flex-row gap-2">
		<button
			class={mode === 'claim' ? 'font-bold' : ''}
			onclick={() => {
				mode = 'claim';
			}}>claim subdomain</button
		>
		<button
			class={mode === 'add' ? 'font-bold' : ''}
			onclick={() => {
				mode = 'add';
			}}>add an external domain (currently doesn't do anything)</button
		>
	</div>
	<div class="mt-2 flex flex-row items-center">
		{#if mode === 'claim'}
			<input type="text" placeholder="subdomain" class="text-right" bind:value={subdomain} /><span
				class="ml-1 text-gray-500">.{page.url.hostname}</span
			>
		{:else if mode === 'add'}
			<span class="mr-0.5 text-right text-gray-500">https://</span>
			<input type="text" placeholder="domain.com" bind:value={externalDomain} />
		{/if}
	</div>
	<h1 class="mt-2 text-red-500">{error}</h1>
	<button
		class="mt-2"
		type="button"
		onclick={() => {
			if (mode === 'claim' && subdomain.trim() !== '') {
				addPage(subdomain.trim(), null);
			} else if (mode === 'add' && externalDomain.trim() !== '') {
				addPage(null, externalDomain.trim());
			}
		}}>Add</button
	>
</div>
