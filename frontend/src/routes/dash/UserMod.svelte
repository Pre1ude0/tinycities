<script lang="ts">
	import type { User } from '$lib/types';
	import { onMount } from 'svelte';
	let d: { user: User } = $props();
	let user = $derived<User>(d.user);
	import BackArrow from '$lib/assets/Back.svelte';

	let editingUsername = $state(false);
	let newUsername = $derived(user.username);
	let newPassword = $state('');
	let confirmPassword = $state('');
	let error = $state<string | null>(null);

	function saveChanges() {
		error = null;

		if (newPassword !== confirmPassword) {
			error = 'Passwords do not match.';
			return;
		}

		const body: Record<string, string> = {};
		if (newUsername !== user.username) body['username'] = newUsername;
		if (newPassword) body['password'] = newPassword;

		fetch('/api/usrmod', {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json', accept: 'application/json' },
			credentials: 'include',
			body: JSON.stringify(body)
		})
			.then(async (res) => {
				if (!res.ok) {
					const response = await res.json().catch(() => null);
					error = response.detail || `Request failed (${res.status})`;
					throw new Error(response.detail || `Request failed (${res.status})`);
				} else {
					window.location.href = '/logout';
				}
			})
			.catch((e) => {
				error = e instanceof Error ? e.message : error;
			});
	}
</script>

<div class="mt-12 flex flex-col gap-3">
	<label class="flex flex-col gap-1">
		<h2 class="text-xl">Change username</h2>
		<div class="flex flex-row gap-2">
			<input
				class="w-1/2"
				type="text"
				bind:value={newUsername}
				placeholder={user.username}
				autocomplete="off"
			/>
			<button
				onclick={() => {
					newUsername = user.username;
				}}
				disabled={newUsername === user.username}
				class="disabled:opacity-60"
			>
				<BackArrow />
			</button>
		</div>
	</label>

	<label class="flex flex-col gap-1"
		><h2 class="text-xl">Change password</h2>
		<div class="flex flex-row gap-2">
			<input
				type="password"
				bind:value={newPassword}
				placeholder="New password"
				autocomplete="new-password"
			/>
			<input
				type="password"
				bind:value={confirmPassword}
				placeholder="Repeat password"
				autocomplete="new-password"
				disabled={!newPassword}
				class="disabled:opacity-60"
			/>
		</div>
	</label>

	{#if error}
		<p class="text-red-400">{error}</p>
	{/if}

	<div class="mt-4 flex flex-row justify-end">
		<button type="button" onclick={saveChanges}> Save & Exit </button>
	</div>
</div>
