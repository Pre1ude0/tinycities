<script lang="ts">
	import { onMount } from 'svelte';
	import type { User } from '$lib/types';
	import AccessKeys from './AccessKeys.svelte';
	import { page } from '$app/state';
	import UserMod from './UserMod.svelte';
	import X from '$lib/assets/X.svelte';

	let usrMod = $derived<boolean>(page.url.hash === '#usrmod');
	let user = $state<User | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function loadWhoAmI() {
		loading = true;
		error = null;

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

			user = (await res.json()) as User;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		await loadWhoAmI();
	});
</script>

<div class="min-h-screen w-screen">
	<div class="flex h-16 w-full items-start justify-between p-6 text-black">
		<div class="flex flex-col items-start gap-1">
			<h1 class="text-2xl font-bold">Dashboard</h1>
			<a class="text-sm text-gray-600" href="#usrmod">@{user?.username || 'user'}</a>
		</div>
		<a href="/logout">Logout</a>
	</div>

	<div class="p-8">
		{#if user && user.role >= 2}
			Access keys
			<AccessKeys />
		{/if}
	</div>
</div>

{#if usrMod && user}
	<div
		class="fixed inset-0 z-50 flex h-screen w-full items-center justify-center shadow-black drop-shadow-lg"
	>
		<div class="relative rounded-sm bg-white p-4">
			<button
				class="absolute top-2 right-2 aspect-square border-0! bg-transparent!"
				onclick={() => (window.location.hash = '')}
				aria-label="Close"
			>
				<X />
			</button>

			<h2 class="text-xl">Settings</h2>
			<UserMod {user} />
		</div>
	</div>
	<button
		aria-label="Close modal"
		onclick={() => (window.location.hash = '')}
		class="fixed inset-0 z-40 h-screen w-screen rounded-none! border-0! bg-black/30! backdrop-blur-lg"
	></button>
{/if}
