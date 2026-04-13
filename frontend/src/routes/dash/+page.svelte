<script lang="ts">
	import { onMount } from 'svelte';

	type WhoAmIResponse = {
		id: number | string;
		username: string;
		role: number;
	};

	let data = $state<WhoAmIResponse | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let keys = $state<string[]>([]);
	let n = $state(1);
	let generating = $state(false);
	let generateError = $state<string | null>(null);

	async function loadWhoAmI() {
		loading = true;
		error = null;
		data = null;

		try {
			const res = await fetch('/api/whoami', {
				method: 'GET',
				headers: { accept: 'application/json' },
				credentials: 'include'
			});

			if (!res.ok) {
				const text = await res.text();
				throw new Error(text || `Request failed (${res.status})`);
			}

			data = (await res.json()) as WhoAmIResponse;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function generateKeys(amount = 1) {
		generating = true;
		generateError = null;

		try {
			const res = await fetch(`/api/generate-key?amount=${encodeURIComponent(String(amount))}`, {
				method: 'GET',
				headers: { accept: 'application/json' },
				credentials: 'include'
			});

			if (!res.ok) {
				const text = await res.text();
				throw new Error(text || `Request failed (${res.status})`);
			}

			const body = (await res.json()) as { access_keys?: string[] };
			if (!Array.isArray(body.access_keys)) throw new Error('Invalid response');

			keys = [...keys, ...body.access_keys];
		} catch (e) {
			generateError = e instanceof Error ? e.message : String(e);
		} finally {
			generating = false;
		}
	}

	onMount(async () => {
		await loadWhoAmI();
	});
</script>

<!-- <center class="mt-30">
	{#if loading}
		<p>Loading...</p>
	{:else if error}
		<p>You're probably not a shmikle binkle</p>
	{:else if data}
		<p>Hello {data.username}</p>
		<p>You are shminkle binkle number {data.id} with permission level {data.role}</p>
		{#if data.role >= 2}
			<div class="mt-3 flex w-fit flex-row gap-1">
				<input class="w-14" type="number" min="1" bind:value={n} />
				<button type="button" onclick={() => generateKeys(n)} disabled={generating}>
					{generating ? 'Generating...' : `Generate ${n} access key(s)`}
				</button>
			</div>
			{#if generateError}
				<p>{generateError}</p>
			{/if}

			Since you are an admin-binkle you can make access keys
			<ul>
				{#each keys as key}
					<li>{key}</li>
				{/each}
			</ul>
		{/if}
	{:else}
		<p>No data</p>
	{/if}
</center> -->

<div class="min-h-screen w-screen">
	<div class="flex h-16 w-full items-center justify-between px-4 text-black">
		<h1 class="text-lg font-bold">Dashboard</h1>
		<a href="/logout" class="hover:underline">Logout</a>
	</div>
</div>
