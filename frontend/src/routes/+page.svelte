<script lang="ts">
	let mode = $state<'login' | 'register'>('login');
	let username = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let inviteKey = $state('');
	let traceback = $state('');
	let tracebackState = $state<'err' | 'success'>('err');

	async function handleSubmit(event: Event) {
		event.preventDefault();

		if (mode === 'register' && password !== confirmPassword) {
			traceback = 'Passwords do not match.';
			tracebackState = 'err';
			return;
		}

		traceback = '';
		tracebackState = 'err';

		try {
			const body =
				mode === 'register'
					? { username, password, access_key: inviteKey }
					: { username, password };

			const res = await fetch(`/api/${mode}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json', accept: 'application/json' },
				credentials: 'include',
				body: JSON.stringify(body)
			});

			let data: any = null;
			try {
				data = await res.json();
			} catch {
				data = null;
			}

			if (!res.ok) {
				const detail =
					typeof data?.detail === 'string'
						? data.detail
						: data?.detail || `Request failed (${res.status})`;
				throw new Error(detail);
			}

			traceback = 'Success! Redirecting...';
			tracebackState = 'success';
			window.location.href = '/whoami';
		} catch (err) {
			traceback = err instanceof Error ? err.message : 'An error occurred.';
			tracebackState = 'err';
		}
	}
</script>

<center class="pt-40">
	<button
		class="cursor-pointer hover:underline"
		onclick={() => (mode = 'register')}
		style:font-weight={mode === 'register' ? 'bold' : 'normal'}
	>
		Register
	</button>
	|
	<button
		class="cursor-pointer hover:underline"
		onclick={() => (mode = 'login')}
		style:font-weight={mode === 'login' ? 'bold' : 'normal'}>Login</button
	>

	<form onsubmit={handleSubmit} class="mt-4 flex flex-col items-center gap-1">
		<input
			id="username"
			type="text"
			bind:value={username}
			placeholder="username"
			autocomplete="off"
			onkeypress={(event) => {
				if (!/[0-9a-zA-Z]/i.test(event.key)) event.preventDefault();
			}}
			required
		/>
		<input id="password" type="password" bind:value={password} placeholder="password" required />

		{#if mode === 'register'}
			<input
				id="confirm"
				type="password"
				bind:value={confirmPassword}
				placeholder="confirm password"
				required
			/>
			<input type="text" placeholder="invite key" bind:value={inviteKey} required />
		{/if}

		<button
			type="submit"
			class="mt-3 cursor-pointer rounded border-2 border-gray-400 bg-gray-100 px-2"
			>{mode === 'login'
				? 'Buy more land on the metaverse'
				: 'Start earning money with atlas earth'}</button
		>
	</form>

	<div
		class="mt-3 block {tracebackState == 'err' ? 'text-red-400' : 'text-green-400'} empty:hidden"
	>
		{traceback}
	</div>
</center>

<style>
	@import 'tailwindcss';

	input {
		@apply rounded-sm border-2 border-gray-400 bg-gray-100 px-1;
	}
</style>
